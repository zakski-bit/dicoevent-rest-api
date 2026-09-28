import os
import uuid
from io import BytesIO
from django.core.cache import cache
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from loguru import logger

from users.permissions import (
    IsEventOrganizerOrAdminOrSuperUser,
    IsOrganizerOrAdminOrSuperUser,
)
from .minio_client import minio_client
from .models import Event, EventPoster
from .pagination import EventPagination
from .serializers import EventPosterSerializer, EventSerializer


def invalidate_event_cache(event_id=None):
    """
    Invalidates all event list caches and the specific detail cache in Redis.
    """
    try:
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern('event_*')
        else:
            cache.delete('event_list_default')
            if event_id:
                cache.delete(f'event_detail_{event_id}')
        logger.info(f"Cache invalidated for event {event_id if event_id else 'all'}")
    except Exception as e:
        logger.warning(f"Error during cache invalidation: {e}")


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('-created_at')
    serializer_class = EventSerializer
    pagination_class = EventPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'location', 'organizer']
    ordering_fields = ['start_time', 'end_time', 'quota', 'created_at', 'name']
    search_fields = ['name', 'description', 'location']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsOrganizerOrAdminOrSuperUser()]
        return [IsEventOrganizerOrAdminOrSuperUser()]

    def list(self, request, *args, **kwargs):
        # Generate cache key based on query params
        query_str = request.GET.urlencode()
        cache_key = f"event_list_{query_str}" if query_str else "event_list_default"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            response = Response(cached_data)
            response['X-Data-Source'] = 'cache'
            return response

        # Query database on cache miss
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_resp = self.get_paginated_response(serializer.data)
            cache.set(cache_key, paginated_resp.data, timeout=3600)
            paginated_resp['X-Data-Source'] = 'database'
            return paginated_resp

        serializer = self.get_serializer(queryset, many=True)
        data = {'events': serializer.data}
        cache.set(cache_key, data, timeout=3600)

        response = Response(data)
        response['X-Data-Source'] = 'database'
        return response

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        cache_key = f"event_detail_{pk}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            response = Response(cached_data)
            response['X-Data-Source'] = 'cache'
            return response

        # Get instance or raise 404 (without cache header)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Store in Redis for 1 hour (3600 seconds)
        cache.set(cache_key, data, timeout=3600)

        response = Response(data)
        response['X-Data-Source'] = 'database'
        return response

    def perform_create(self, serializer):
        event = serializer.save()
        invalidate_event_cache(event.id)
        user_name = self.request.user.username if self.request.user.is_authenticated else 'unknown'
        logger.info(f"Event {event.id} created by {user_name}")

    def perform_update(self, serializer):
        event = serializer.save()
        invalidate_event_cache(event.id)
        user_name = self.request.user.username if self.request.user.is_authenticated else 'unknown'
        logger.info(f"Event {event.id} updated by {user_name}")

    def perform_destroy(self, instance):
        event_id = instance.id
        instance.delete()
        invalidate_event_cache(event_id)
        user_name = self.request.user.username if self.request.user.is_authenticated else 'unknown'
        logger.info(f"Event {event_id} deleted by {user_name}")


class PosterUploadView(APIView):
    """
    POST /api/events/upload/
    Uploads event poster image to MinIO and records filename in database.
    Validations:
    - MIME type: Must be image type (starts with 'image/')
    - Size: Maximum 500 kB (500 * 1024 bytes)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_IMAGE_TYPES = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/jpg',
        'image/svg+xml',
    ]
    MAX_FILE_SIZE = 500 * 1024  # 500 kB

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        event_id = request.data.get('event')

        if not image_file:
            return Response(
                {'error': 'Image file is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not event_id:
            return Response(
                {'error': 'Event ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate MIME type
        content_type = getattr(image_file, 'content_type', '')
        if not content_type or not (content_type.startswith('image/') or content_type in self.ALLOWED_IMAGE_TYPES):
            return Response(
                {'error': f'Invalid file format. Uploaded file must be an image. Received {content_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (max 500 kB)
        if image_file.size > self.MAX_FILE_SIZE:
            return Response(
                {'error': f'File too large. Maximum size allowed is 500 kB ({self.MAX_FILE_SIZE} bytes). Uploaded: {image_file.size} bytes.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify event exists
        try:
            event = Event.objects.get(id=event_id)
        except (Event.DoesNotExist, ValueError):
            return Response(
                {'error': 'Event not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate unique filename for MinIO
        ext = os.path.splitext(image_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"

        try:
            # Upload to MinIO
            minio_client.upload_file(
                file_obj=image_file,
                object_name=unique_filename,
                content_type=content_type
            )

            # Store in database
            poster = EventPoster.objects.create(
                event=event,
                image=unique_filename
            )

            logger.info(f"Poster {poster.id} ({unique_filename}) uploaded for event {event.id}")

            return Response(
                {
                    'id': str(poster.id),
                    'image': poster.image
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error uploading poster: {e}")
            return Response(
                {'error': f'Failed to upload poster: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EventPosterView(APIView):
    """
    GET /api/events/<event_id>/poster/
    Retrieves all posters for an event.
    """
    permission_classes = [AllowAny]

    def get(self, request, event_id, *args, **kwargs):
        try:
            event = Event.objects.get(id=event_id)
        except (Event.DoesNotExist, ValueError):
            return Response(
                {'error': 'Event not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        posters = event.posters.all()
        serializer = EventPosterSerializer(posters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ServeMediaView(APIView):
    """
    GET /api/media/<filename>/
    Streams uploaded media files directly from MinIO.
    """
    permission_classes = [AllowAny]

    def get(self, request, filename, *args, **kwargs):
        try:
            minio_resp = minio_client.get_object(filename)
            content_type = minio_resp.headers.get('content-type', 'image/jpeg')
            return HttpResponse(minio_resp.read(), content_type=content_type)
        except Exception as e:
            logger.error(f"Error serving media file {filename}: {e}")
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)
