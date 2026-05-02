from datetime import date
from .models import UserSubscription

def check_subscription(user):
    # superuser always allowed
    if user.is_superuser:
        return True

    try:
        sub = UserSubscription.objects.get(user=user)

        # अगर inactive है
        if not sub.is_active:
            return False

        # अगर expiry date निकल गई
        if sub.end_date and sub.end_date < date.today():
            sub.is_active = False
            sub.save()
            return False

        return True

    except UserSubscription.DoesNotExist:
        return False