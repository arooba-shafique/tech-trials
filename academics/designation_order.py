from django.db.models import Case, When, Value, IntegerField


def apply_designation_ordering(qs, designation_field='designation', name_field='full_name'):
    """Order a queryset by designation category: Management, Administration, Teachers, Janitorial.

    designation_field / name_field allow ordering across relations, e.g.
    apply_designation_ordering(qs, 'employee__designation', 'employee__full_name').
    """
    mgmt = ['vp', 'group_head', 'section_head', 'manager', 'assistant_manager', 'a_coordinator']
    admin = ['team_lead', 'coordinator', 'accountant', 'fdc']
    teachers = ['teacher']
    janitorial = ['aya', 'sweeper', 'office_boy', 'compositer', 'photocopier']

    whens = []
    for desig in mgmt:
        whens.append(When(**{designation_field: desig}, then=Value(1)))
    for desig in admin:
        whens.append(When(**{designation_field: desig}, then=Value(2)))
    for desig in teachers:
        whens.append(When(**{designation_field: desig}, then=Value(3)))
    for desig in janitorial:
        whens.append(When(**{designation_field: desig}, then=Value(4)))

    return qs.annotate(
        desig_order=Case(*whens, default=Value(5), output_field=IntegerField())
    ).order_by('desig_order', name_field)


def _apply_designation_ordering(qs):
    """Apply ordering by designation category: Management, Administration, Teachers, Janitorial."""
    return apply_designation_ordering(qs)
