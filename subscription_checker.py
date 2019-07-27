from app.models import Company, Subscription, db
from app import create_app
from datetime import datetime


app = create_app('production')


if __name__ == '__main__':
    with app.app_context():
        all_companies = Company.query.all()
        for company in all_companies:
            last_subscription = Subscription.query.filter_by(
                company_id=company.id).order_by(Subscription.id.desc()).first()
            expired = last_subscription is None or last_subscription\
                .end_date.date() < datetime.utcnow().date()
            if expired:
                company.subscription_active = False
            db.session.add(company)
        db.session.commit()
