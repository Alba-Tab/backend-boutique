import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio para enviar notificaciones push usando Firebase Cloud Messaging"""

    _initialized = False

    @classmethod
    def _initialize_firebase(cls):
        """Inicializar Firebase Admin SDK - solo una vez"""
        if not cls._initialized and not firebase_admin._apps:
            try:
                # Ruta del archivo de credenciales
                cred_path = settings.FIREBASE_CREDENTIAL_PATH

                # Verificar que existe el archivo
                if not os.path.exists(cred_path):
                    logger.error("Archivo firebase-credentials.json no encontrado")
                    return False

                # Inicializar Firebase
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)

                cls._initialized = True
                logger.info("Firebase Admin SDK inicializado correctamente")
                return True

            except Exception as e:
                logger.error(f"Error inicializando Firebase: {str(e)}")
                return False

        return True

    @classmethod
    def send_to_token(cls, token, title, body, data=None):
        """
        Enviar notificación a un token específico

        Args:
            token (str): Token FCM del dispositivo
            title (str): Título de la notificación
            body (str): Mensaje de la notificación
            data (dict): Datos adicionales (opcional)

        Returns:
            bool: True si se envió correctamente, False si falló
        """
        if not cls._initialize_firebase():
            return False

        try:
            # Crear el mensaje
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )

            # Enviar mensaje
            response = messaging.send(message)
            logger.info(f"Notificación enviada exitosamente. ID: {response}")
            return True

        except messaging.UnregisteredError:
            logger.warning(f"Token FCM inválido o expirado: {token}")
            return False
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return False

    @classmethod
    def send_to_user(cls, usuario, title, body, data=None):
        """
        Enviar notificación a un usuario específico

        Args:
            usuario: Instancia del modelo Usuario
            title (str): Título de la notificación
            body (str): Mensaje de la notificación
            data (dict): Datos adicionales (opcional)

        Returns:
            bool: True si se envió correctamente, False si falló
        """
        if not hasattr(usuario, 'fcm_token') or not usuario.fcm_token:
            logger.warning(f"Usuario {usuario.username} no tiene token FCM")
            return False

        return cls.send_to_token(
            token=usuario.fcm_token,
            title=title,
            body=body,
            data=data
        )

    @classmethod
    def send_to_role(cls, role, title, body, data=None):
        """
        Enviar notificación a todos los usuarios de un rol específico

        Args:
            role (str): Rol de usuario (cliente, vendedor, admin)
            title (str): Título de la notificación
            body (str): Mensaje de la notificación
            data (dict): Datos adicionales (opcional)

        Returns:
            int: Número de notificaciones enviadas exitosamente
        """
        if not cls._initialize_firebase():
            return 0

        from apps.usuarios.models import Usuario

        # Obtener usuarios con el rol específico y token FCM
        usuarios = Usuario.objects.filter(
            rol=role,
            activo=True,
            fcm_token__isnull=False
        ).exclude(fcm_token='')

        success_count = 0
        for usuario in usuarios:
            if cls.send_to_user(usuario, title, body, data):
                success_count += 1

        logger.info(f"Notificaciones enviadas a {success_count}/{usuarios.count()} usuarios del rol '{role}'")
        return success_count

    @classmethod
    def send_to_multiple_tokens(cls, tokens, title, body, data=None):
        """
        Enviar notificación a múltiples tokens usando multicast

        Args:
            tokens (list): Lista de tokens FCM
            title (str): Título de la notificación
            body (str): Mensaje de la notificación
            data (dict): Datos adicionales (opcional)

        Returns:
            dict: Diccionario con información del envío
        """
        if not cls._initialize_firebase():
            return {'success_count': 0, 'failure_count': len(tokens)}

        if not tokens:
            logger.warning("Lista de tokens vacía")
            return {'success_count': 0, 'failure_count': 0}

        try:
            # Crear mensaje multicast
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )

            # Enviar a todos los tokens - FUNCIÓN CORRECTA para v7.x
            response = messaging.send_each_for_multicast(message)

            logger.info(f"Notificaciones enviadas: {response.success_count}/{len(tokens)}")

            # Manejar tokens inválidos
            failed_tokens = []
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(tokens[idx])
                        logger.warning(f"Token fallido: {tokens[idx]} - Error: {resp.exception}")

                # Limpiar tokens inválidos
                cls._cleanup_invalid_tokens(failed_tokens)

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failed_tokens': failed_tokens
            }

        except Exception as e:
            logger.error(f"Error enviando notificaciones múltiples: {str(e)}")
            return {'success_count': 0, 'failure_count': len(tokens)}

    @classmethod
    def _cleanup_invalid_tokens(cls, invalid_tokens):
        """
        Limpiar tokens FCM inválidos de la base de datos

        Args:
            invalid_tokens (list): Lista de tokens inválidos
        """
        if not invalid_tokens:
            return

        try:
            from apps.usuarios.models import Usuario

            updated_count = Usuario.objects.filter(
                fcm_token__in=invalid_tokens
            ).update(fcm_token=None)

            logger.info(f"Limpiados {updated_count} tokens FCM inválidos de la base de datos")

        except Exception as e:
            logger.error(f"Error limpiando tokens inválidos: {str(e)}")

    @classmethod
    def send_venta_notification(cls, usuario, venta_id, mensaje=""):
        """
        Método específico para notificaciones de ventas

        Args:
            usuario: Usuario que realizó la compra
            venta_id: ID de la venta
            mensaje (str): Mensaje personalizado

        Returns:
            bool: True si se envió correctamente
        """
        title = "Venta Registrada"
        body = mensaje if mensaje else f"Tu pedido #{venta_id} ha sido registrado exitosamente"

        data = {
            'type': 'venta',
            'venta_id': str(venta_id),
            'timestamp': str(timezone.now())
        }

        return cls.send_to_user(usuario, title, body, data)
