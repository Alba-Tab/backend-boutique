from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from .models import Usuario
from .serializers import UsuarioSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rol', 'activo']

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def registro(self, request):
        """Registrar nuevo usuario"""
        try:
            usuario = Usuario.objects.create_user(
                username=request.data['username'],
                email=request.data['email'],
                password=request.data['password'],
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
                telefono=request.data.get('telefono', ''),
                rol=request.data.get('rol', 'cliente')
            )
            refresh = RefreshToken.for_user(usuario)

            return Response({
                'user': UsuarioSerializer(usuario).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'] , permission_classes=[AllowAny])
    def login(self, request):
        """Login de usuario"""
        usuario = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if usuario:
            refresh = RefreshToken.for_user(usuario)
            return Response({
                'user': UsuarioSerializer(usuario).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtener datos del usuario autenticado"""
        return Response(UsuarioSerializer(request.user).data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout - Blacklistea el refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({'message': 'Logout exitoso'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def actualizar_perfil(self, request):
        """El usuario actualiza su propia información"""
        usuario = request.user

        # Campos permitidos para actualizar
        campos_permitidos = ['first_name', 'last_name', 'email', 'telefono']

        # Validar email único (si lo está cambiando)
        nuevo_email = request.data.get('email')
        if nuevo_email and nuevo_email != usuario.email:
            if Usuario.objects.filter(email=nuevo_email).exists():
                return Response(
                    {'error': 'Este email ya está registrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Actualizar solo campos permitidos
        for campo in campos_permitidos:
            if campo in request.data:
                setattr(usuario, campo, request.data[campo])

        usuario.save()

        return Response({
            'message': 'Perfil actualizado exitosamente',
            'user': UsuarioSerializer(usuario).data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def cambiar_password(self, request):
        """Cambiar contraseña del usuario autenticado"""
        usuario = request.user
        password_actual = request.data.get('password_actual')
        password_nueva = request.data.get('password_nueva')
        password_confirmacion = request.data.get('password_confirmacion')

        # Validaciones
        if not password_actual or not password_nueva or not password_confirmacion:
            return Response(
                {'error': 'Todos los campos son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar contraseña actual
        if not usuario.check_password(password_actual):
            return Response(
                {'error': 'La contraseña actual es incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que las nuevas contraseñas coincidan
        if password_nueva != password_confirmacion:
            return Response(
                {'error': 'Las contraseñas nuevas no coinciden'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar longitud mínima
        if len(password_nueva) < 8:
            return Response(
                {'error': 'La contraseña debe tener al menos 8 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que no sea igual a la actual
        if password_actual == password_nueva:
            return Response(
                {'error': 'La nueva contraseña debe ser diferente a la actual'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cambiar la contraseña
        usuario.set_password(password_nueva)
        usuario.save()

        return Response({
            'message': 'Contraseña actualizada exitosamente'
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def actualizar_token_fcm(self, request):
        """Actualizar token FCM para notificaciones push"""
        usuario = request.user
        fcm_token = request.data.get('fcm_token')

        if not fcm_token:
            return Response(
                {'error': 'fcm_token es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.fcm_token = fcm_token
        usuario.save()

        return Response({
            'message': 'Token FCM actualizado exitosamente'
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def eliminar_token_fcm(self, request):
        """Eliminar token FCM (cuando cierra sesión o desinstala app)"""
        usuario = request.user
        usuario.fcm_token = None
        usuario.save()

        return Response({
            'message': 'Token FCM eliminado exitosamente'
        })
