import django_filters
from django_filters import DateFilter, CharFilter, ChoiceFilter
from .models import Game

def __init__(self, *args, **kwargs):
    for key in self.filters.iteritems():
        self.filters[key[0]].extra.update(
            {'help_text': ''}
        )

class FilterCronologia(django_filters.FilterSet):
    player1 = CharFilter(field_name='player1__username', lookup_expr='icontains')
    player2 = CharFilter(field_name='player2__username', lookup_expr='icontains')
    mode = ChoiceFilter(choices=Game.MODE_CHOICES)
    winner = CharFilter(field_name='winner__username', lookup_expr='icontains')

    class Meta:
        model = Game
        fields = ['player1', 'player2', 'mode', 'winner']
        
        
