from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from blog.constaints import NUMBER_OF_POSTS
from blog.forms import CommentForm, PostForm, ProfileForm
from blog.models import Category, Comment, Post, User
from blog.mixins import (
    DispatchCommentMixin, GetProfileMixin, PostMixin, UrlCommentsMixin
)


class IndexListView(ListView):
    '''Главная страница.'''

    model = Post
    form_class = PostForm
    template_name = 'blog/index.html'
    paginate_by = NUMBER_OF_POSTS

    def get_queryset(self):
        queryset = Post.objects.select_related(
            'location', 'author', 'category'
        ).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
        return queryset


class PostDetailView(DetailView):
    '''Страница отдельного поста.'''

    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if post.author == self.request.user:
            return post
        if not (post.is_published & post.category.is_published):
            raise Http404('''Страница поста снятого'с публикации
                           доступна только автору''')
        if post.pub_date > timezone.now():
            raise Http404('Страница отложенного поста доступна только автору')
        return post


class CategoryListView(ListView):
    '''Страница категории.'''

    model = Post
    template_name = 'blog/category.html'
    paginate_by = NUMBER_OF_POSTS

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        self.category = get_object_or_404(
            Category, slug=category_slug, is_published=True
        )
        return self.category.posts.select_related(
            'author', 'location', 'category',
        ).filter(is_published=True, pub_date__lte=timezone.now()
                 ).annotate(comment_count=Count('comments')
                            ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(GetProfileMixin, ListView):
    '''Страница профиля пользователя.'''

    model = User
    form_class = ProfileForm
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_object(self):
        return get_object_or_404(User,
                                 username=self.kwargs['slug'])

    def get_queryset(self):
        user = self.get_object()
        if user == self.request.user:
            queryset = user.posts.all().order_by('-pub_date')
        else:
            queryset = user.posts.filter(
                pub_date__lte=timezone.now()
            ).order_by('-pub_date')
        queryset = queryset.annotate(comment_count=Count('comments'))
        return queryset


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    '''Страница редактирования страницы профиля пользователя.'''

    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user])


class PostCreateView(LoginRequiredMixin, CreateView):
    '''Страница написания поста.'''

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user])


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):
    '''Страница изменения поста.'''

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:profile')

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']},
        )


class PostDeleteView(
    LoginRequiredMixin, PostMixin, DeleteView, GetProfileMixin
     ):
    '''Страница удаления поста.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''Страница написания комментария.'''

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs['pk']])

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['pk'])
        return super().form_valid(form)


class CommentUpdateView(
    LoginRequiredMixin, UrlCommentsMixin, DispatchCommentMixin, UpdateView
     ):
    '''Страница обновления комментария.'''

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class CommentDeleteView(
    LoginRequiredMixin, UrlCommentsMixin, DispatchCommentMixin, DeleteView
     ):
    '''Страница удаления комментария.'''

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'id'
