"""MinIO Client Configuration"""
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
from datetime import timedelta
import io
import json


KNOWN_BUCKETS = ["documentos", "evidencias", "reportes", "avatars"]

# Política de lectura pública para el bucket avatars
_PUBLIC_READ_POLICY = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"AWS": ["*"]},
        "Action": ["s3:GetObject"],
        "Resource": ["arn:aws:s3:::avatars/*"]
    }]
})


class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        # Cliente para URLs externas (accesibles desde el navegador)
        self.external_client = Minio(
            settings.MINIO_EXTERNAL_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        # Pre-poblar el cache de regiones para evitar llamadas de red al endpoint
        # externo (que no es accesible desde dentro de Docker). Sin esto, cada
        # llamada a presigned_get_object() haría un GET /bucket?location= a
        # 192.168.x.x:9000, bloqueando el event loop de asyncio por ~5 minutos.
        for bucket in KNOWN_BUCKETS:
            self.external_client._region_map[bucket] = "us-east-1"
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Crear buckets necesarios si no existen"""
        buckets = ["documentos", "evidencias", "reportes"]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"✓ Bucket '{bucket}' creado")
            except S3Error as e:
                print(f"Error al crear bucket '{bucket}': {e}")
        
        # Bucket avatars con lectura pública
        try:
            if not self.client.bucket_exists("avatars"):
                self.client.make_bucket("avatars")
                print("✓ Bucket 'avatars' creado")
            # Aplicar política pública siempre (idempotente)
            self.client.set_bucket_policy("avatars", _PUBLIC_READ_POLICY)
        except S3Error as e:
            print(f"Error al configurar bucket 'avatars': {e}")

    def upload_avatar(self, user_id: int, data: bytes, content_type: str) -> str:
        """Sube foto de perfil a MinIO y retorna la URL pública directa."""
        ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
        ext = ext_map.get(content_type, "jpg")
        object_name = f"avatar_{user_id}.{ext}"
        data_stream = io.BytesIO(data)
        self.client.put_object("avatars", object_name, data_stream, length=len(data), content_type=content_type)
        # URL directa pública: http(s)://<external_endpoint>/avatars/<object>
        scheme = "https" if settings.MINIO_SECURE else "http"
        return f"{scheme}://{settings.MINIO_EXTERNAL_ENDPOINT}/avatars/{object_name}"

    
    def upload_file(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream"):
        """Subir un archivo a MinIO"""
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Error al subir archivo: {e}")
            raise
    
    def get_presigned_url(self, bucket_name: str, object_name: str, expires: int = 3600):
        """Generar URL pre-firmada para descargar un archivo"""
        try:
            # Usar el cliente externo para generar URLs accesibles desde el navegador
            url = self.external_client.presigned_get_object(
                bucket_name, 
                object_name, 
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            print(f"Error al generar URL: {e}")
            raise
    
    def delete_file(self, bucket_name: str, object_name: str):
        """Eliminar un archivo de MinIO"""
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error al eliminar archivo: {e}")
            raise


# Instancia global del cliente MinIO
minio_client = MinIOClient()
