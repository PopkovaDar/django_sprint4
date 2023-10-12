from django.shortcuts import redirect, get_object_or_404
from .models import Post


class PostMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=self.kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
