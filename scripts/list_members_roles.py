import os
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
    django.setup()
    from membership.models import Member
    print(f"{'User':<30} {'Role':<25} {'Club':<25} {'Status':<10}")
    print('-' * 90)
    for member in Member.objects.select_related('user', 'club').all():
        user_str = member.user.username if member.user else 'N/A'
        club_str = member.club.name if member.club else 'N/A'
        print(f"{user_str:<30} {member.get_role_display():<25} {club_str:<25} {member.status:<10}")

if __name__ == '__main__':
    main()
