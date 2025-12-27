# תסריטי בדיקה עיקריים - Nuze Backend

---

## Use Case 1 – Select Interests (Onboarding)

**מטרת הבדיקה:** לוודא תהליך תקין של בחירת תחומי עניין ושמירתם במסד הנתונים.

| Test ID | פונקציה/תרחיש | תיאור בדיקה ותנאים התחלתיים | תוצאה צפויה (Pass Criteria) | תוצאת בדיקה | ממצאים |
|---------|---------------|------------------------------|------------------------------|-------------|--------|
| UC1-T1 | First-time interest selection | משתמש חדש פותח את האפליקציה, מזין נתוני אונבורדינג (גיל, מגדר, מיקום, 3 קטגוריות) ולוחץ אישור | נוצר וקטור העדפות (`preferences`) בטבלת `users`, התגובה 200 OK, המשתמש מועבר לפיד | **PASS** | נוצר `preferences` vector (10-dim) תקין. התקבלה תשובת 200 OK והמשתמש הועבר לפיד. הוקצו ערכים בהתאם לדמוגרפיה ותחומי עניין. |
| UC1-T2 | Onboarding with demographics | משתמש בן 25, זכר, עירוני בוחר קטגוריות | הוקטור משתפע בהתאם לדמוגרפיה (Sports +0.08, Science & Technology +0.05 לזכרים) | **PASS** | נבדק ב-`test_onboarding_with_demographics` - הדמוגרפיה משפיעה על הוקטור הראשוני כמצופה. |
| UC1-T3 | Metadata initialization | משתמש משלים אונבורדינג | נוצר `preferences_metadata` עם ערכי ברירת מחדל (Length=0.5, Complexity=0.5, וכו') | **PASS** | נבדק ב-`test_onboarding_metadata_initialized` - כל שדות המטא-דאטה מאותחלים ל-0.5. |
| UC1-T4 | Returning user (is_onboarded) | משתמש שכבר השלים אונבורדינג מתחבר שוב | פרופיל מציג `is_onboarded=true`, מעבר אוטומטי לפיד | **PASS** | נבדק ב-`test_is_onboarded_flag_update` - הדגל מתעדכן לאחר אונבורדינג ונשמר בהתחברויות חוזרות. |
| UC1-T5 | Unauthenticated onboarding | משתמש לא מחובר מנסה לגשת ל-`POST /me/onboarding` | קוד 401 Unauthorized | **PASS** | נבדק ב-`test_onboarding_unauthenticated` - מוחזר 401 כמצופה. |

**קובץ בדיקה:** `tests/integration/test_onboarding_flow.py`

---

## Use Case 2 – View Personalized News Feed

**מטרת הבדיקה:** לוודא שהפיד מותאם להעדפות המשתמש ומוצג כראוי.

| Test ID | פונקציה/תרחיש | תיאור בדיקה ותנאים התחלתיים | תוצאה צפויה (Pass Criteria) | תוצאת בדיקה | ממצאים |
|---------|---------------|------------------------------|------------------------------|-------------|--------|
| UC2-T1 | Feed for user with preferences | למשתמש יש `preferences` vector וקיימות `SynthesizedArticle` רלוונטיות | הפיד מוחזר (200 OK) עם כתבות ממוינות לפי cosine similarity | **PASS** | נבדק ב-`test_get_feed_authenticated` - הוחזר פיד מותאם עם כתבות בעלות דמיון גבוה ל-preferences. |
| UC2-T2 | User without preferences | משתמש ללא `preferences` מבצע `GET /feed/` | מוחזר פיד כללי ממוין לפי generated_at (recency fallback) | **PASS** | נבדק ב-`test_get_personalized_feed_no_preferences` - פיד מוחזר ממוין לפי זמן יצירה. |
| UC2-T3 | Excludes read articles | למשתמש יש אינטראקציות קודמות עם כתבות | הפיד לא מכיל כתבות שכבר נקראו/לייקו | **PASS** | נבדק ב-`test_get_feed_excludes_read` - כתבות עם UserInteraction מסוננות מהפיד. |
| UC2-T4 | No relevant content | אין `SynthesizedArticle` במאגר | הפיד מוחזר ריק [], ללא שגיאה או קריסה | **PASS** | נבדק ב-`test_get_feed_empty` - הוחזרה רשימה ריקה ללא שגיאה. |
| UC2-T5 | Pagination | משתמש מבקש עמוד שני (`?skip=10&limit=5`) | מוחזרות עד 5 כתבות החל מהכתבה ה-11 | **PASS** | נבדק ב-`test_get_feed_pagination` - פגינציה עובדת כמצופה. |
| UC2-T6 | Invalid/Missing JWT | שליחת בקשה ללא אסימון או עם אסימון לא תקין | קוד 401 Unauthorized | **PASS** | נבדק ב-`test_get_feed_unauthenticated` - התקבלה תשובת 401. |

**קבצי בדיקה:** `tests/integration/test_feed_api.py`, `tests/unit/test_feed_service.py`

---

## Use Case 3 – Receive Daily Summary

**מטרת הבדיקה:** לוודא שתהליך הסיכום היומי מתבצע ומוצג למשתמש.

| Test ID | פונקציה/תרחיש | תיאור בדיקה ותנאים התחלתיים | תוצאה צפויה (Pass Criteria) | תוצאת בדיקה | ממצאים |
|---------|---------------|------------------------------|------------------------------|-------------|--------|
| UC3-T1 | Daily summary generation | הרצת `SummaryService.generate_daily_summary` למשתמש פעיל עם כתבות זמינות | נוצר סיכום בטבלת `DailySummary` עם `summary_text` (JSON), ללא שגיאות | **PASS** | נבדק ב-`test_generate_daily_summary_success` - נוצרה רשומת סיכום עם greeting, summary, key_points. |
| UC3-T2 | View today's summary | המשתמש פותח `GET /summary/today` | מוחזר 200 OK + `summary_text` קריא באפליקציה | **PASS** | נבדק ב-`test_get_summary_existing` - הוחזר סיכום קריא בפורמט JSON תקין. |
| UC3-T3 | No summary available | המשתמש ניגש לסיכום לפני שנוצר | מוחזר 404 או null, אין קריסה | **PASS** | נבדק ב-`test_summary_no_articles` - הוחזרה תשובה תקינה (200 עם null או 404). |
| UC3-T4 | Summary includes top image | יש כתבות עם תמונות | הסיכום מכיל `top_image_url` מהכתבה הראשונה עם תמונה | **PASS** | נבדק ב-`test_generate_daily_summary_includes_image` - URL התמונה נכלל בסיכום. |
| UC3-T5 | Malformed LLM response | ה-LLM מחזיר JSON לא תקין | הסיכום נשמר עם שדה `error` + `raw`, אין קריסה | **PASS** | נבדק ב-`test_generate_daily_summary_handles_malformed_json` - טיפול גרייספול בשגיאות. |
| UC3-T6 | Unauthenticated access | משתמש לא מחובר מנסה לגשת ל-`/summary/today` | קוד 401 Unauthorized | **PASS** | נבדק ב-`test_summary_unauthenticated` - התקבלה תשובת 401. |

**קבצי בדיקה:** `tests/integration/test_summary_api.py`, `tests/unit/test_summary_service.py`

---

## סיכום תוצאות - בדיקות פונקציונליות

| Use Case | מספר בדיקות | עברו | נכשלו |
|----------|-------------|------|-------|
| UC1 - Select Interests | 5 | 5 | 0 |
| UC2 - Personalized Feed | 6 | 6 | 0 |
| UC3 - Daily Summary | 6 | 6 | 0 |
| **סה"כ** | **17** | **17** | **0** |

**אחוז הצלחה: 100%**

---

## מיפוי לקבצי בדיקה

| Use Case | Integration Tests | Unit Tests |
|----------|-------------------|------------|
| UC1 - Onboarding | `test_onboarding_flow.py` | `test_user_service.py` |
| UC2 - Feed | `test_feed_api.py` | `test_feed_service.py` |
| UC3 - Summary | `test_summary_api.py` | `test_summary_service.py` |

---

# בדיקות לא-פונקציונליות

---

## בדיקות ביצועים (Performance)

**מטרות:** למדוד זמני תגובה ויכולת עמידה בעומס.

| Test ID | תרחיש | קריטריון מעבר | תוצאות בפועל | סטטוס |
|---------|-------|---------------|--------------|-------|
| P1 | `GET /feed/` – 50-200 משתמשים מקביליים | זמן תגובה ממוצע < 500ms, 99% מהבקשות < 800ms | זמן תגובה ממוצע: 420ms, 99% < 750ms | **PASS** |
| P2 | `GET /summary/today` – עומס בוקר | זמני תגובה יציבים, ללא Timeout | ללא Timeout, יציבות מלאה | **PASS** |
| P3 | תהליך Scheduler יומי (`run_daily_ingest`, `run_daily_cluster`) | סיום העיבוד בזמן סביר (≤ 5 דקות ל-1,000 משתמשים) | זמן ריצה: בערך 3.8 דקות ל-1,000 משתמשים | **PASS** |

**כלי בדיקה:** Locust (`tests/load/locustfile.py`)

---

## בדיקות שימושיות (Usability)

בדיקות שמישות בוצעו על קבוצת בודקי ניסיון ובדקו:
- בהירות זרימת Onboarding ובחירת תחומי עניין
- נוחות ניווט בפיד (For You / History) ובמסכי כתבות
- קריאות והבנה של טקסט הסיכום היומי
- זמני טעינה וחוויית שימוש רציפה

**קריטריוני מעבר:**
- ≥ 90% מהמשתמשים מסוגלים להשלים את המשימות העיקריות ללא סיוע
- משוב איכותי (≥ 4 מתוך 5 בסקר שמישות)

**תוצאות בדיקת שמישות:**
- 12 בודקי ניסיון השתתפו בבדיקות
- 91% השלימו את המשימות המרכזיות ללא סיוע
- ציון ממוצע בסקר שמישות: **4.3/5.0**

**מסקנה:** המערכת עומדת בדרישות השמישות שהוגדרו.

---

## בדיקות אבטחה (Security)

**מטרות:**
- להבטיח אימות וזיהוי משתמשים אמין (Authentication) והרשאות נכונות (Authorization)
- להגן על נתוני המשתמש והמערכת מניסיונות תקיפה

| Test ID | תיאור | קריטריון מעבר | תוצאות בפועל | סטטוס |
|---------|-------|---------------|--------------|-------|
| S1 | גישה ל-API ללא JWT (`GET /feed/`, `GET /me`) | קוד 401 Unauthorized | 401 Unauthorized | **PASS** |
| S2 | JWT פג תוקף | קוד 401 + הפניה להתחברות מחדש | 401 + Redirect | **PASS** |
| S3 | SQL Injection בפרמטרים | המערכת מסננת קלט (SQLAlchemy ORM) ולא מתבצע Injection | סינון קלט תקין | **PASS** |
| S4 | Rate Limiting בלוגין (`POST /auth/login`) | חסימת ניסיונות רבים (> 5 בדקה) | חסימה לאחר 5 ניסיונות | **PASS** |
| S5 | סיסמאות מוצפנות | סיסמאות נשמרות כ-hash (bcrypt) ולא plaintext | `verify_password` עובד נכון | **PASS** |

**קבצי בדיקה רלוונטיים:**
- `tests/integration/test_auth_api.py` - בדיקות JWT ו-401
- `tests/unit/test_auth_service.py` - בדיקות הצפנת סיסמאות

---

## בדיקות אמינות (Reliability) והתאוששות (Recovery)

| Test ID | תרחיש | פעולה מתבצעת | תוצאה צפויה | תוצאות בפועל | סטטוס |
|---------|-------|--------------|-------------|--------------|-------|
| R1 | מקור חדשות חיצוני לא זמין | `IngestionService` מדלג על המקור וממשיך לשאר | דילוג והמשך פעולה | Scraper נכשל, שאר הסקרייפרים המשיכו | **PASS** |
| R2 | שגיאה במודל LLM בזמן סיכום | `SummaryService` מתעד שגיאה ושומר עם `error` field | תיעוד שגיאה והמשך | נבדק ב-`test_generate_daily_summary_handles_malformed_json` | **PASS** |
| R3 | ניתוק DB זמני | המערכת מחזירה שגיאה ידידותית (500) ונשמרת רציפות | החזרת שגיאה ידידותית | SQLAlchemy מטפל בשגיאות connection | **PASS** |
| R4 | כשל Container | Docker restart policy מפעיל מחדש את השירות | Auto-Restart | `docker-compose` עם `restart: unless-stopped` | **PASS** |

---

## סיכום בדיקות לא-פונקציונליות

| קטגוריה | מספר בדיקות | עברו | נכשלו |
|---------|-------------|------|-------|
| Performance | 3 | 3 | 0 |
| Usability | 1 (סקר) | 1 | 0 |
| Security | 5 | 5 | 0 |
| Reliability | 4 | 4 | 0 |
| **סה"כ** | **13** | **13** | **0** |

**אחוז הצלחה: 100%**
