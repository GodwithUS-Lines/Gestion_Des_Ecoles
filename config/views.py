from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Page d'accueil publique"""
    features = [
        {
            'title': 'Gestion des élèves',
            'description': 'Inscriptions, dossiers, suivi scolaire et bulletins.',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>'
        },
        {
            'title': 'Gestion des enseignants',
            'description': 'Affectations, emplois du temps, matières et classes.',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>'
        },
        {
            'title': 'Notes & Absences',
            'description': 'Saisie des notes, calcul des moyennes, suivi des absences.',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>'
        },
        {
            'title': 'Paiements & Frais',
            'description': 'Facturation, encaissements, bourses, réductions.',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
        },
        {
            'title': 'Emploi du temps',
            'description': 'Planification des cours, salles, créneaux, conflits.',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>'
        },
        {
            'title': 'Rapports & Statistiques',
            'description': 'Tableaux de bord, exports, indicateurs de performance.',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>'
        },
    ]
    stats = {
        'schools': 0,
        'students': 0,
        'teachers': 0,
        'classes': 0,
    }
    return render(request, 'home.html', {
        'features': features,
        'stats': stats,
    })


@login_required
def dashboard(request):
    """Dashboard principal (protégé)"""
    stats = [
        {
            'label': 'Total élèves',
            'value': '0',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>',
            'bg_class': 'bg-blue-500'
        },
        {
            'label': 'Total enseignants',
            'value': '0',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>',
            'bg_class': 'bg-green-500'
        },
        {
            'label': 'Total classes',
            'value': '0',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5z"></path>',
            'bg_class': 'bg-yellow-500'
        },
        {
            'label': 'Total écoles',
            'value': '0',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>',
            'bg_class': 'bg-purple-500'
        },
    ]
    quick_actions = [
        {
            'label': 'Nouvel élève',
            'url': '#',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path>',
            'bg_class': 'bg-blue-500'
        },
        {
            'label': 'Nouvel enseignant',
            'url': '#',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>',
            'bg_class': 'bg-green-500'
        },
        {
            'label': 'Nouvelle classe',
            'url': '#',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path>',
            'bg_class': 'bg-yellow-500'
        },
        {
            'label': 'Saisir notes',
            'url': '#',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path>',
            'bg_class': 'bg-purple-500'
        },
    ]
    return render(request, 'dashboard.html', {
        'user': request.user,
        'stats': stats,
        'quick_actions': quick_actions,
    })