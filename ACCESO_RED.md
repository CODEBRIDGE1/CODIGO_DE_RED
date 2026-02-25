# 🌐 Acceso en Red Local - Código de Red

## 📍 IP del Servidor
**IP:** `192.168.100.14`

## 🔗 URLs de Acceso

### Desde CUALQUIER PC en la red (incluida esta Mac):

- **🖥️ Aplicación Frontend:** http://192.168.100.14:5173
- **⚙️ API Backend:** http://192.168.100.14:8001
- **📚 Documentación API:** http://192.168.100.14:8001/docs
- **💾 MinIO (Storage):** http://192.168.100.14:9001

## 👤 Credenciales de Prueba

**Usuario Admin:**
- Email: `admin@tenant-demo.com`
- Password: `Admin123!`

**Superadmin:**
- Email: `superadmin@codebridge.mx`
- Password: `SuperAdmin123!`

## ⚠️ Notas Importantes

1. **Firewall:** Asegúrate que el firewall de la Mac permita conexiones en los puertos:
   - 5173 (Frontend)
   - 8001 (API)
   - 9001 (MinIO Console)

2. **Red:** Todas las PCs deben estar en la misma red local (192.168.100.x)

3. **Cache del navegador:** Si ya intentaste acceder antes, limpia el cache:
   - Chrome/Edge: `Ctrl+Shift+Delete` (Windows) o `Cmd+Shift+Delete` (Mac)
   - Firefox: `Ctrl+Shift+Delete` (Windows) o `Cmd+Shift+Delete` (Mac)
   - Safari: `Cmd+Option+E` (Mac)

4. **No uses localhost:** Desde otras PCs SIEMPRE usa la IP `192.168.100.14`

## 🔧 Verificar Conectividad

Desde la otra PC, abre una terminal/CMD y ejecuta:

```bash
# Windows
ping 192.168.100.14
curl http://192.168.100.14:8001/docs

# Mac/Linux
ping 192.168.100.14
curl -I http://192.168.100.14:8001/docs
```

Si el ping funciona pero curl no, revisa el firewall de la Mac.

## 🔥 Configurar Firewall en Mac (si es necesario)

1. Abre **Preferencias del Sistema** > **Seguridad y privacidad** > **Firewall**
2. Click en **Opciones del Firewall**
3. Asegúrate que Docker esté permitido
4. O desactiva temporalmente el firewall para pruebas

## 🚨 Troubleshooting

### Error "NetworkError" o "Connection Refused"
1. Verifica que Docker esté corriendo: `docker ps`
2. Verifica los contenedores:
   ```bash
   docker logs codigo_red_api --tail 20
   docker logs codigo_red_frontend --tail 20
   ```
3. Reinicia los servicios:
   ```bash
   cd /Users/ernestoherrera/Desktop/CODIGO_DE_RED
   docker-compose restart
   ```

### No carga la página
1. Limpia cache del navegador
2. Abre la consola del navegador (F12) y revisa errores
3. Verifica que estés usando la IP correcta (192.168.100.14)

### La IP cambió
Si la Mac obtiene una IP diferente (por DHCP):
1. Verifica la nueva IP: `ipconfig getifaddr en0`
2. Actualiza los archivos:
   - `/Users/ernestoherrera/Desktop/CODIGO_DE_RED/.env` (CORS_ORIGINS y MINIO_EXTERNAL_ENDPOINT)
   - `/Users/ernestoherrera/Desktop/CODIGO_DE_RED/frontend/.env` (VITE_API_BASE_URL)
3. Reinicia: `docker-compose restart api frontend`
