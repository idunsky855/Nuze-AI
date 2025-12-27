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

## סיכום תוצאות

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
