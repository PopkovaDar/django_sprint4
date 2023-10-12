from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from blog.models import Category, Comment, Post, User
from .forms import CommentForm, PostForm, ProfileForm
from .constaints import NUMBER_OF_POSTS


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_count'] = Comment.objects.annotate(Count('id'))
        return context


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
    model = Category
    template_name = 'blog/category.html'
    paginate_by = NUMBER_OF_POSTS

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(
            Category, slug=category_slug, is_published=True
        )
        return category.posts.select_related(
            'author', 'location', 'category',
        ).filter(is_published=True, pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category.objects.values('id', 'title', 'description').filter(
                is_published=True
            ),
            slug=self.kwargs['category_slug'],
        )
        context['category'] = category
        return context


class ProfileListView(ListView):
    '''Страница профиля пользователя.'''
    model = User
    form_class = ProfileForm
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_object(self):
        return get_object_or_404(User,
                                 username=self.kwargs['slug'])

    def get_queryset(self):
        return self.get_object().posts.all().order_by(
            '-pub_date').annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        return dict(
            super().get_context_data(**kwargs),
            profile=self.get_object(),
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    '''Страница редактирования страницы профиля пользователя.'''
    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

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
    success_url = reverse_lazy('blog:profile')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       args=[self.request.user])


class PostUpdateView(LoginRequiredMixin, UpdateView):
    '''Страница изменения поста.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('blog:profile')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']},
        )

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    '''Страница удаления поста.'''
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(LoginRequiredMixin, CreateView):
    '''Страница написания комментария.'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    queryset = Comment.objects
    pk_url_kwarg = 'pk'
    posts = None

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.posts.pk},
        )

    def dispatch(self, request, *args, **kwargs):
        self.posts = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.posts
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    '''Страница обновления комментария.'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', instance.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    '''Страница удаления комментария.'''
    model = Comment
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:comment')
    pk_url_kwarg = 'id'

    def dispatch(self, request, *args, **kwargs):
        comment_pk = self.kwargs.get(self.pk_url_kwarg)
        author = get_object_or_404(self.model, pk=comment_pk).author
        if author != self.request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        self.post_data = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})
