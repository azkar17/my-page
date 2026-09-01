# Brief: Add live URLs to portfolio projects

## Repo
C:/Users/azkar/my-page (already cloned, clean working tree)

## Task
In `index.html`, inside the `CONFIG.projects` array, add a `url` field to exactly 3 project entries. The site already renders a link chip when `url` is present (see lines ~995-997 and ~1063-1065) — no other code changes needed.

### 1. Noderight Dental (line ~644-649)
- Currently has comment: `// url intentionally omitted — the public site isn't linked. Was: https://noderightdental.com`
- ADD: `url:"https://noderightdental.com",` as the first field inside the object (after `{ name:"Noderight Dental", img:"noderight-dental",`)
- REMOVE the "url intentionally omitted" comment line above it
- Keep everything else (desc, long, stack, gallery) unchanged

### 2. MAPA Circular Management System (line ~650-654)
- ADD: `url:"https://members.mapa.net.my",` as first field inside the object
- Keep everything else unchanged

### 3. Speggit Order (line ~666-670)
- ADD: `url:"https://order.speggit.my",` as first field inside the object
- Keep everything else unchanged

## Constraints
- DO NOT touch any other project entries (Jom Mancing, Liga FA, Tim Katang, Solar Referral, Trello-Strutt stay as-is)
- DO NOT touch any other file
- DO NOT change desc/long/stack/gallery text
- DO NOT commit or push — leave changes uncommitted for review
- Match the existing code style: double quotes, same indentation (4 spaces), comma after url value

## Verify
After editing, confirm:
1. `grep -n "url:" index.html` shows exactly 3 new url lines (plus the existing comment lines about url in the docs block)
2. The 3 urls are exactly: https://noderightdental.com, https://members.mapa.net.my, https://order.speggit.my
3. No other project entries were modified (git diff shows only the 3 intended blocks)
