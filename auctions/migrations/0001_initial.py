# Initial schema for BIDWAVE.
import decimal
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Auction', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('title', models.CharField(max_length=160)),
            ('description', models.TextField(blank=True)),
            ('category', models.CharField(default='Collectibles', max_length=50)),
            ('image_url', models.URLField(blank=True)),
            ('starting_price', models.DecimalField(decimal_places=2,max_digits=12,validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
            ('current_price', models.DecimalField(decimal_places=2,max_digits=12)),
            ('minimum_increment', models.DecimalField(decimal_places=2,default=decimal.Decimal('1.00'),max_digits=12,validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
            ('status', models.CharField(choices=[('ACTIVE','Live'),('CLOSED','Ended')],default='ACTIVE',max_length=8)),
            ('ends_at', models.DateTimeField(db_index=True)),
            ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ('version', models.PositiveIntegerField(default=0)),
            ('seller', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='listed_auctions',to=settings.AUTH_USER_MODEL)),
            ('highest_bidder', models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='leading_auctions',to=settings.AUTH_USER_MODEL)),
            ('winner', models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='won_auctions',to=settings.AUTH_USER_MODEL)),
        ], options={'ordering':['-created_at']}),
        migrations.CreateModel(name='Bid',fields=[
            ('id', models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('amount',models.DecimalField(decimal_places=2,max_digits=12)),
            ('request_key',models.UUIDField(unique=True)),
            ('created_at',models.DateTimeField(default=django.utils.timezone.now)),
            ('auction',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='bids',to='auctions.auction')),
            ('bidder',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ],options={'ordering':['-id']}),
        migrations.AddIndex(model_name='auction',index=models.Index(fields=['status','ends_at'],name='auctions_au_status_5a34c1_idx')),
    ]
