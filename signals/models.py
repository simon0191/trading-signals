from django.db import models
from django.utils import timezone
from enum import Enum

class OperationType(Enum):
  SELL = "SELL"
  BUY = "BUY"

class Signal(models.Model):
  ticker = models.CharField(max_length=15)
  operation_type = models.CharField(
    max_length=50,
    choices=[(op_type, op_type.value) for op_type in OperationType]
  )
  potential_gain = models.DecimalField(max_digits=6, decimal_places=2)
  potential_loss = models.DecimalField(max_digits=6, decimal_places=2)
  analysis = models.TextField()
  created_at = models.DateTimeField()

  def risk_reward_ratio(self):
    return self.potential_gain/self.potential_loss

  def __str__(self):
    return f"Signal({self.operation_type} {self.ticker})"
