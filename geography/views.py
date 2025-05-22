from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import WorldSportsBody

login_decorator = method_decorator(login_required, name='dispatch')

@login_decorator
class WorldSportsBodyListView(ListView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_list.html'
    context_object_name = 'worldsportsbodies'

@login_decorator
class WorldSportsBodyDetailView(DetailView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_detail.html'
    context_object_name = 'worldsportsbody'

@login_decorator
class WorldSportsBodyCreateView(CreateView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:worldsportsbody-list')

@login_decorator
class WorldSportsBodyUpdateView(UpdateView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:worldsportsbody-list')

@login_decorator
class WorldSportsBodyDeleteView(DeleteView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_confirm_delete.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')