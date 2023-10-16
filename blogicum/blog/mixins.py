from django.shortcuts import redirect, reverse


class PostMixin:

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', pk=post.pk)
        return super().dispatch(request, *args, **kwargs)


class UrlCommentsMixin:

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class GetProfileMixin:

    def get_context_data(self, **kwargs):
        return dict(
            super().get_context_data(**kwargs),
            profile=self.get_object(),
        )


class DispatchCommentMixin:
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != request.user:
            return redirect('blog:post_detail', self.object.post_id)
        return super().dispatch(request, *args, **kwargs)
