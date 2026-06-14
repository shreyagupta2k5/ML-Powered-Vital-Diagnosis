# VitalDX Frontend — Manual Test Checklist
**Version:** 1.0.0
**Date:** June 2026
**Test before:** Every demo or handoff

---

## 1. Login Flow
- [ ] Visit `localhost:5173` → redirects to `/dashboard` → redirects to `/login` (no token)
- [ ] Enter any username + password → clicks Sign in → redirects to `/dashboard`
- [ ] Visit `/login` when already logged in → redirects away to `/dashboard`
- [ ] Click Sign out → redirects to `/login` → can't access `/dashboard` without logging in again

## 2. Dashboard Page
- [ ] Patient table loads with 10 patients
- [ ] Patients sorted by risk (CRITICAL first, then HIGH, MODERATE, LOW)
- [ ] CRITICAL badge is red, HIGH is amber, MODERATE is orange, LOW is green
- [ ] Risk score progress bars fill correctly (PT-007 bar should be longest)
- [ ] Sidebar shows correct counts for Critical / High / Moderate / Low
- [ ] Search "PT-007" → only PT-007 shows in table
- [ ] Search "PT-999" → "No patients match" empty state shows
- [ ] Click CRITICAL filter → only CRITICAL patients show
- [ ] Click ALL → all patients show again
- [ ] Stat cards show correct numbers (Total: 10, Critical/High: 4, Moderate: 3, Low: 3)

## 3. Navigation
- [ ] Clicking a patient row → navigates to `/patient/PT-007`
- [ ] Clicking Dashboard in sidebar → stays on `/dashboard`
- [ ] Clicking Admin/MLOps in sidebar → navigates to `/admin/mlops`
- [ ] ← Dashboard button on Patient page → goes back to dashboard
- [ ] ← Dashboard button on Admin page → goes back to dashboard

## 4. Alert Bell & Drawer
- [ ] Bell icon visible in navbar
- [ ] After 30 seconds → bell badge shows "1" (mock alert fires)
- [ ] Clicking bell → Alert Drawer slides in from right
- [ ] Drawer shows alert type, patient ID, timestamp
- [ ] Clicking "Mark all read" → badge disappears, drawer shows "all read ✓"
- [ ] Clicking a HIGH_RISK alert → navigates to that patient page
- [ ] Clicking "Clear all alerts" → drawer empties
- [ ] Clicking overlay → drawer closes

## 5. Patient Detail Page
- [ ] Visit `/patient/PT-007` → loads without error
- [ ] Risk banner shows CRITICAL in red with score 0.85
- [ ] Track 1 card shows 67% mortality, HIGH badge
- [ ] Track 2 card shows 31% crisis, MODERATE badge
- [ ] Track 3 card shows SpO2 Drop 87% (red bar), Tachycardia 12%, Hypotension 4%
- [ ] SHAP chart shows 6 features, sao2_mean bar is longest (red)
- [ ] Vital signs show HR, MAP, SpO2 sparklines
- [ ] Time range buttons (1h / 6h / 24h) are clickable
- [ ] Visit `/patient/PT-999` → "Patient not found" screen shows
- [ ] "← Back to Dashboard" button on not-found screen works

## 6. Admin / MLOps Panel
- [ ] Visit `/admin/mlops` → loads without error
- [ ] System Health shows Track 1 (green), Track 2 (green), Track 3 (orange/degraded)
- [ ] Overall status shows "DEGRADED"
- [ ] Drift Monitor defaults to Track 2 tab
- [ ] Track 2 drift shows "1 feature drifted" warning
- [ ] glucose_mean bar is red (alert), others are blue
- [ ] Switching to Track 1 tab → no drift warning, all bars blue
- [ ] Model Registry dropdown shows 3 tracks
- [ ] Selecting a track → shows version, AUC, F1, Recall
- [ ] Hot-swap button → ConfirmModal appears
- [ ] Clicking Cancel → modal closes, nothing happens
- [ ] Clicking Confirm → modal closes, success alert appears

## 7. Error Handling
- [ ] Refresh any page → stays on same page (ProtectedRoute + localStorage token)
- [ ] Open browser console → no red errors on any page
- [ ] Manually break a component → ErrorBoundary shows "Something went wrong" screen
- [ ] "Refresh page" button on ErrorBoundary → reloads correctly

## 8. General
- [ ] App works on Chrome
- [ ] App works on Edge
- [ ] No console errors on any page
- [ ] All pages load under 2 seconds
- [ ] Mock data mode note visible at bottom of dashboard

---

## Sign-off
| Tester | Date | Result |
|--------|------|--------|
| | | |
| | | |