from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import FilmWork
from movies.models import Roles


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ['get']

    def get_queryset(self):
        queryset = FilmWork.objects.values('id', 'title', 'description', 'creation_date', 'rating', 'type').order_by(
            '-creation_date'
        )
        queryset = queryset.annotate(
            genres=ArrayAgg('persons__full_name', distinct=True),
            actors=ArrayAgg('persons__full_name', distinct=True, filter=Q(personfilmwork__role=Roles.ACTOR)),
            directors=ArrayAgg('persons__full_name', distinct=True, filter=Q(personfilmwork__role=Roles.DIRECTOR)),
            writers=ArrayAgg('persons__full_name', distinct=True, filter=Q(personfilmwork__role=Roles.WRITER)),
        )
        return queryset

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, self.paginate_by)
        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,
            'results': list(queryset),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_context_data(self, **kwargs):
        return self.object
