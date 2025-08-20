# תיעוד מניפסטים של Kubernetes/OpenShift

🌍 **שפה:** [English](README.md) | **[עברית](README.he.md)**

מדריך זה מסביר את התפקיד של כל אחד מקבצי ה-YAML בתיקייה זו, איך הם עובדים יחד, ומה עושה כל חלק חשוב.

## סקירה כללית

האפליקציה מורכבת משני רכיבים עיקריים:
1. **MongoDB** - מסד הנתונים
2. **FastAPI** - ה-API שמתחבר למסד הנתונים

יש לנו **שני מסלולי פריסה**:
- **Deployment** - הדרך הסטנדרטית (קבצים רגילים)
- **StatefulSet** - הדרך המומלצת למסדי נתונים (קבצים עם 'a')

---

## רכיבים משותפים (לשני המסלולים)

### `00-mongo-configmap.yaml` - הגדרות לא רגישות
```yaml
data:
  MONGO_INITDB_ROOT_USERNAME: "mongoadmin"    # שם משתמש ראשי
  MONGO_DB_NAME: "enemy_soldiers"             # שם מסד הנתונים (לפי הדרישות!)
  MONGO_COLLECTION_NAME: "soldier_details"   # שם הקולקשן (לפי הדרישות!)
```
**למה ConfigMap?** מידע לא רגיש שאפשר לראות, קל לשנות בלי לבנות מחדש את האימג'.

### `01-mongo-secret.yaml` - סיסמאות מוצפנות
```yaml
data:
  MONGO_INITDB_ROOT_PASSWORD: amhzZHl0dGZlNjVmZHM1NHNjZjY1  # מוצפן base64
```
**למה Secret?** סיסמאות חייבות להיות מוצפנות. OpenShift מצפין אותן אוטומטית.

---

## מסלול 1: פריסה עם Deployment (קבצים רגילים)

### `02-mongo-pvc.yaml` - דרישת אחסון
```yaml
spec:
  accessModes:
    - ReadWriteOnce    # רק pod אחד יכול לכתוב
  resources:
    requests:
      storage: 2Gi     # דורש 2GB אחסון קבוע
```
**למה PVC?** בלי זה, כל הנתונים של MongoDB יאבדו כשה-pod נהרג.

### `03-mongo-deployment.yaml` - הרצת MongoDB
**חלקים חשובים:**
```yaml
# איזה אימג' להשתמש
image: docker.io/library/mongo:8.0

# איך לקבל את ההגדרות
envFrom:
  - configMapRef:
      name: mongo-db-config     # כל המשתנים מה-ConfigMap
  - secretRef:
      name: mongo-db-credentials # כל המשתנים מה-Secret

# בדיקות בריאות - מה ההבדל בין השתיים?
readinessProbe:                # "האם מוכן לקבל תעבורה?"
  exec:
    command: ["mongosh", "--eval", "db.adminCommand('ping')"]
  initialDelaySeconds: 10      # ממתין 10 שניות אחרי שהpod עולה
  periodSeconds: 10           # בודק כל 10 שניות
  timeoutSeconds: 5           # אם לא עונה תוך 5 שניות - נכשל
  failureThreshold: 3         # אחרי 3 כשלונות - מפסיק לשלוח תעבורה (לא הורג!)

livenessProbe:                 # "האם עדיין חי?"
  exec:
    command: ["mongosh", "--eval", "db.adminCommand('ping')"]
  initialDelaySeconds: 30      # ממתין 30 שניות (יותר!) - נותן זמן להתחיל
  periodSeconds: 15           # בודק כל 15 שניות (פחות תדיר)
  timeoutSeconds: 5           # זמן המתנה לתשובה
  failureThreshold: 3         # אחרי 3 כשלונות - הורג את הpod ויוצר חדש!

# ניהול משאבים - כמה CPU וזיכרון צריך
resources:
  requests:                   # "מינימום מובטח" - OpenShift מבטיח שיהיה זמין
    cpu: "200m"              # 200 מילי-cores = 0.2 ליבת CPU
    memory: "256Mi"          # 256 מגהבייט RAM
  limits:                     # "מקסימום מותר" - לא יכול לחרוג
    cpu: "500m"              # 0.5 ליבת CPU מקסימום - אם חורג, OpenShift מאט
    memory: "512Mi"          # 512 מגהבייט RAM מקסימום - אם חורג, OpenShift הורג!

# חיבור לאחסון הקבוע
volumeMounts:
  - name: mongo-persistent-storage
    mountPath: /data/db        # איפה MongoDB שומר את הנתונים
volumes:
  - name: mongo-persistent-storage
    persistentVolumeClaim:
      claimName: mongo-db-pvc  # מתחבר ל-PVC שיצרנו
```

### `04-mongo-service.yaml` - כתובת פנימית למונגו
```yaml
spec:
  selector:
    app.kubernetes.io/instance: mongo-db  # מחבר לכל הpods עם התווית הזו
  ports:
    - port: 27017              # פורט סטנדרטי של MongoDB
      targetPort: 27017
```
**מה זה עושה?** יוצר כתובת `mongo-db-service:27017` שה-API יכול להשתמש בה.

### `05-fastapi-deployment.yaml` - הרצת ה-API
**חלקים חשובים:**
```yaml
# איזה אימג' להשתמש (זה מוחלף בסקריפט הפריסה)
image: "docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest"

# משתני סביבה שה-API צריך
env:
  - name: MONGO_HOST
    value: "mongo-db-service"    # שם ה-Service של MongoDB
  - name: MONGO_PORT
    value: "27017"
  - name: MONGO_USER
    valueFrom:
      configMapKeyRef:           # לוקח מה-ConfigMap
        name: mongo-db-config
        key: MONGO_INITDB_ROOT_USERNAME
  - name: MONGO_PASSWORD
    valueFrom:
      secretKeyRef:              # לוקח מה-Secret (מוצפן!)
        name: mongo-db-credentials
        key: MONGO_INITDB_ROOT_PASSWORD

# בדיקות בריאות של ה-API - שני endpoints שונים!
readinessProbe:               # "האם מוכן לעבוד?"
  httpGet:
    path: /health             # בודק גם חיבור למסד נתונים - אם MongoDB מנותק, נכשל!
    port: 8080
  initialDelaySeconds: 15     # ממתין 15 שניות אחרי שהpod עולה
  periodSeconds: 10          # בודק כל 10 שניות

livenessProbe:               # "האם עדיין חי?"
  httpGet:
    path: /                  # בודק רק שהשרת עונה - לא בודק מסד נתונים
    port: 8080
  initialDelaySeconds: 20     # ממתין 20 שניות (יותר מreadiness!)
  periodSeconds: 20          # בודק כל 20 שניות (פחות תדיר)

# ניהול משאבים - ה-API צריך פחות מMongoDB
resources:
  requests:                  # מינימום מובטח
    cpu: "50m"              # 0.05 ליבת CPU - יישום Python קל
    memory: "128Mi"         # 128 מגהבייט RAM
  limits:                    # מקסימום מותר
    cpu: "200m"             # 0.2 ליבת CPU מקסימום
    memory: "256Mi"         # 256 מגהבייט RAM מקסימום
```

### `06-fastapi-service.yaml` - כתובת פנימית ל-API
```yaml
spec:
  selector:
    app.kubernetes.io/instance: mongo-api  # מחבר לpods של ה-API
  ports:
    - port: 8080
      targetPort: 8080
```

### `07-fastapi-route.yaml` - כתובת ציבורית
```yaml
spec:
  to:
    kind: Service
    name: mongo-api-service    # מפנה לService של ה-API
  tls:
    termination: edge          # HTTPS אוטומטי
    insecureEdgeTerminationPolicy: Redirect  # מפנה HTTP ל-HTTPS
```
**מה זה עושה?** יוצר URL ציבורי כמו `https://mongo-api-route-xxx.apps.cluster.com`

---

## מסלול 2: פריסה עם StatefulSet (קבצים עם 'a')

### למה StatefulSet טוב יותר למסדי נתונים?
1. **זהות יציבה** - כל pod מקבל שם קבוע (mongo-db-statefulset-0)
2. **סדר פריסה** - pods עולים ויורדים בסדר מוגדר
3. **אחסון אוטומטי** - יוצר PVC אוטומטית לכל pod

### `03a-mongo-statefulset.yaml` - StatefulSet במקום Deployment
**הבדלים עיקריים:**
```yaml
kind: StatefulSet              # במקום Deployment
spec:
  serviceName: "mongo-db-headless-service"  # צריך Headless Service

# במקום volumes רגיל:
volumeClaimTemplates:          # יוצר PVC אוטומטית!
- metadata:
    name: mongo-persistent-storage
  spec:
    accessModes: [ "ReadWriteOnce" ]
    resources:
      requests:
        storage: 2Gi
```

### `04a-mongo-headless-service.yaml` - Service מיוחד ל-StatefulSet
```yaml
spec:
  clusterIP: None              # זה מה שעושה אותו "headless"
```
**למה headless?** StatefulSet צריך את זה כדי לתת לכל pod כתובת ייחודית.

### קבצי API מותאמים (05a, 06a, 07a)
ההבדל היחיד:
```yaml
# בקבצים רגילים:
name: mongo-api
value: "mongo-db-service"

# בקבצים של StatefulSet:
name: mongo-api-stateful
value: "mongo-db-headless-service"
```

---

## איך לבחור בין המסלולים?

### השתמש ב-Deployment אם:
- אתה מתחיל ורוצה משהו פשוט
- לא אכפת לך מאבדן נתונים (לפיתוח)
- יש לך רק MongoDB אחד

### השתמש ב-StatefulSet אם:
- אתה רוצה מסד נתונים יציב (production)
- חשוב לך שהנתונים ישרדו
- תכנן להגדיל ל-replica set של MongoDB בעתיד

---

## סדר הפעלה נכון

### Deployment:
```bash
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml
oc apply -f 02-mongo-pvc.yaml
oc apply -f 03-mongo-deployment.yaml
oc apply -f 04-mongo-service.yaml
# המתן שMongoDB יהיה מוכן
oc apply -f 05-fastapi-deployment.yaml
oc apply -f 06-fastapi-service.yaml
oc apply -f 07-fastapi-route.yaml
```

### StatefulSet:
```bash
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml
oc apply -f 03a-mongo-statefulset.yaml
oc apply -f 04a-mongo-headless-service.yaml
# המתן שMongoDB יהיה מוכן
oc apply -f 05a-fastapi-deployment-for-statefulset.yaml
oc apply -f 06a-fastapi-service-for-statefulset.yaml
oc apply -f 07a-fastapi-route-for-statefulset.yaml
```

---

## בדיקת תקינות

### בדיקה שהכל עובד:
```bash
# בדוק שכל הpods רצים
oc get pods

# בדוק שהservices זמינים
oc get svc

# קבל את ה-URL הציבורי
oc get route

# בדוק שה-API עובד
curl https://your-route-url/health
```

### פתרון בעיות נפוצות:
```bash
# אם pod לא עולה
oc describe pod <pod-name>
oc logs <pod-name>

# אם אין חיבור למסד נתונים
oc exec -it <mongo-pod> -- mongosh
```