from django.db.models import Case, When, Value, IntegerField


def _apply_designation_ordering(qs):
    """Apply ordering by designation category: Management, Administration, Teachers, Janitorial."""
    mgmt = [
        'vp', 'group_head', 'section_head', 'manager', 'assistant_manager', 'a_coordinator',
        'director', 'manager_academics', 'hr_manager', 'assistant_manager_academics'
    ]
    admin = ['team_lead', 'coordinator', 'accountant', 'fdc']
    teachers = ['teacher']
    janitorial = ['aya', 'sweeper', 'office_boy', 'compositer', 'photocopier']

    whens = []
    for desig in mgmt:
        whens.append(When(designation=desig, then=Value(1)))
    for desig in admin:
        whens.append(When(designation=desig, then=Value(2)))
    for desig in teachers:
        whens.append(When(designation=desig, then=Value(3)))
    for desig in janitorial:
        whens.append(When(designation=desig, then=Value(4)))

    return qs.annotate(
        desig_order=Case(*whens, default=Value(5), output_field=IntegerField())
    ).order_by('desig_order', 'full_name')
