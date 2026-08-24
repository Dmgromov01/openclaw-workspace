# DESIGN SPEC — R2D2 UI

## 1. Font stack
```css
font-family: Inter, -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
```

## 2. Core tokens
```css
:root {
  --bg: #f7f8fa;
  --surface: #ffffff;
  --surface-subtle: #f3f5f7;
  --border: #e6e9ee;
  --border-strong: #d9dee6;
  --text: #121826;
  --text-muted: #6b7280;
  --accent: #5b6cff;
  --accent-soft: #eef1ff;
  --radius-card: 20px;
  --radius-card-lg: 24px;
  --radius-icon: 999px;
  --shadow-soft: 0 8px 24px rgba(16, 24, 40, 0.04);
}
```

## 3. Spacing
- Внешние поля экрана: `16px`
- Вертикальный gap между большими блоками: `12px`
- Padding внутри карточек: `14–16px`
- Gap внутри service row: `12px`
- Section inset для grouped list: `12px`

## 4. Heights
- Header Telegram shell: `56–60px`
- Summary strip: `44–48px`
- Weather block: `108–124px`
- Translator block: `88–104px`
- Service row: `60–68px`
- Tab bar: `72–78px`

## 5. Radii
- Summary: `18px`
- Weather card: `22–24px`
- Translator card: `20–22px`
- Service list container: `22px`
- Individual rows inside list: `16px` if visually split
- Circular icon container: `36–42px`, full radius

## 6. Icon sizes
- Верхние summary/status icons: `14–16px`
- Weather supporting icons: `18–22px`
- Service icons: `18–20px` inside circular container `36–42px`
- Tab bar icons: `20–22px`

## 7. Typography scale
- App title: `22px / 700`
- Card section title: `17px / 600`
- Main weather temp: `32–36px / 700`
- Row title: `15px / 600`
- Secondary/meta: `12–13px / 500`
- Tiny label: `11px / 600`

## 8. Service list pattern
```text
┌──────────────────────────────┐
│  ○  Дайджест           >     │
│     3 новых выжимки          │
├──────────────────────────────┤
│  ○  Поездки            >     │
│     Плеяды / активный поиск  │
├──────────────────────────────┤
│  ○  OpenClaw Search    >     │
│     2 активных поиска        │
├──────────────────────────────┤
│  ○  Викторина          >     │
│     Проверь себя            │
└──────────────────────────────┘
```

## 9. Visual hierarchy
1. Weather block — главный hero.
2. Summary strip — короткий status layer.
3. Translator block — primary utility block.
4. Services list — structured grouped utilities.
5. Tab bar — secondary navigation.

## 10. Do / Don’t
### Do
- Use grouped list surfaces.
- Use circular icon holders.
- Keep colors restrained.
- Make weather graphics soft and premium.
- Build hierarchy with spacing, grouping, contrast.

### Don’t
- Don’t use emoji icons.
- Don’t overuse bright accent colors.
- Don’t bring back tile-heavy dashboard grid.
- Don’t add heavy shadows.
- Don’t make borders too dark or too thick.
