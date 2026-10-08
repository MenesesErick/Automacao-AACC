from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Acesso exclusivo ao Administrador da plataforma (is_superuser).

    Usado no lugar de IsAdminUser porque coordenadores também possuem
    is_staff=True (para diferenciá-los dos alunos) e, portanto, passariam
    na checagem padrão do DRF (que verifica apenas is_staff).
    """

    message = "Apenas administradores podem executar esta ação."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_superuser)
