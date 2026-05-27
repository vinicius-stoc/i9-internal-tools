from django.db.models import Max

from rdo.models import RDO


class RDOService:
    @staticmethod
    def proximo_numero(obra):
        ultimo_numero = RDO.objects.filter(obra=obra).aggregate(maior=Max('numero'))['maior'] or 0
        return ultimo_numero + 1

    @staticmethod
    def total_efetivo(rdo):
        return sum(item.quantidade or 0 for item in rdo.efetivos.all())
