from django.contrib import admin

from .models import Category, Comment, Location, Post


class BlogAdmin(admin.ModelAdmin):
    """Панель администратора."""

    list_editable = ('is_published',)


@admin.register(Category)
class CategoryAdmin(BlogAdmin):
    """Управление катерогиями со страницы админа."""

    list_display = (
        'title',
        'is_published',
        'created_at',
        'slug',
    )


@admin.register(Post)
class PostAdmin(BlogAdmin):
    """Управление постами со страницы админа."""

    list_display = (
        'title',
        'is_published',
        'created_at',
        'text',
        'pub_date',
        'author',
        'location',
        'category',
    )


@admin.register(Location)
class AdminLocation(BlogAdmin):
    """Управление местоположением со страницы админа."""

    list_display = (
        'created_at',
        'is_published',
        'name',
    )


@admin.register(Comment)
class AdminComment(BlogAdmin):
    """Управление комментариями со страницы админа."""
    list_display = (
        'created_at',
        'post',
        'text',
        'author',
    )
    list_editable = ['text']
