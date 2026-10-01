from django.db import models
from users.models import Store
from inventory.models import Product

class AIRecommendation(models.Model):
    URGENT_REORDER = 'URGENT_REORDER'
    OVERSTOCK = 'OVERSTOCK'
    OPTIMAL = 'OPTIMAL'
    RECOMMENDATION_TYPES = [
        (URGENT_REORDER, 'Urgent Reorder'),
        (OVERSTOCK, 'Overstock'),
        (OPTIMAL, 'Optimal'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='ai_recommendations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ai_recommendations')
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    explanation = models.TextField()
    recommended_order_quantity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.get_recommendation_type_display()}] {self.product.name}"
