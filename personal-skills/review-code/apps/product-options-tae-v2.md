# App Profile: product-options-tae-v2

> Repo: SAPO/tae-v2 — Storefront Runtime V2 của OPTIS Product Options (Theme App Extension). Song song với V1 (`tae`); backend ở `product-options-api`.

## Kiến trúc & luồng chính
- Stack: TypeScript strict + Lit (custom element, light DOM) + vitest + webpack. Mỗi Option Type là một element `optis-po-<type>-option` kế thừa `OptisPoBaseOptionElement`.
- Tách 2 tầng: **rule nghiệp vụ thuần** ở `src/modules/core/option-set/<domain>/` (vd `date-time/`: availability, serialize, format hiển thị) và **element + helper thuần DOM** ở `src/modules/core/option-types/<type>/`. Element chỉ gọi vào tầng rule, không tự tính rule.
- Một Instance = một OptionSet trên một product. Dữ liệu cấu hình đi một chiều: `createAppContext` → `InstanceManager` → `InstanceContext` → `OptionSetInstance`, rồi ra hai nhánh: `optionContext` (cho element) và `CartPropertiesSource` (cho `buildCartProperties` → cart property đi vào order). Thêm một giá trị dùng chung cho cả field lẫn order thì phải đi qua cả hai nhánh.
- **Plan gating (từ OPOS-162):** quyền do backend resolve (bảng plan CMS ∪ `shops.features_unlocked`) và phát trong Store Config `entitlements`; storefront KHÔNG giữ bảng plan. Luồng: Liquid in `entitlements` → `AppConfig.entitlements` (raw) → `resolvePlanEntitlements` (parse ở boundary; thiếu/sai → không gate) → `InstanceManager.mount` → `applyPlanEntitlements` (thuần, gỡ field theo feature, không bỏ Option/choice). Option set `isFreePremium` bỏ qua gate. Diff thêm feature gate mới phải chạm cả api (`StorefrontPlanFeatureV2` + resolver) lẫn tae-v2 (`PLAN_FEATURES` + gate) và đối chiếu cách editor cms *thật sự* khoá feature đó. — `Áp dụng khi: logic`
- `extensions/option-app-extensions/assets/optis-po-style-v2.css` là file **SINH TỰ ĐỘNG** từ `styles/*.css` bằng `npm run build:styles` — sửa nguồn trong `styles/`, không sửa tay file asset; diff phải có asset khớp nguồn.

## Quy ước bắt buộc của app
- Nguồn quy ước chính: `openspec/specs/code-convention/spec.md` (có spec theo từng Option Type ở `openspec/specs/option-*`). Chấm theo file này, không áp chuẩn ngoài. — `Áp dụng khi: logic, structure`
- Hàm dùng **object parameter** khi có ≥3 tham số, nhiều giá trị cùng type, hoặc có optional parameter. — `Áp dụng khi: logic`
- Boolean mở đầu `is/has/can/should/was`; handler nội bộ `handle*`, callback/prop `on*`. — `Áp dụng khi: logic`
- **CSS class không được làm JS hook** — dùng element ref hoặc `data-optis-po-*`; data attribute phải có tiền tố `data-optis-po-`. — `Áp dụng khi: ui`
- Element đọc value từ `this.state`, **ghi qua `this.commitValue()`** (không gọi thẳng `context.setOptionValue`). — `Áp dụng khi: logic, ui`
- **Không global mutable state** (biến module-level ghi được); cấu hình theo trang/Instance phải đi qua context. Cache thuần theo khoá cố định (vd cache Intl theo locale) là ngoại lệ chấp nhận được. — `Áp dụng khi: logic`
- Giao diện/màu đi qua CSS variables (token `--optis-po-*` trong `styles/optis-po-tokens.css`), không hard-code hex trong rule. — `Áp dụng khi: ui, config`
- **Test nằm trong `tests/` của domain** và **không có cycle giữa hai folder** (kể cả cạnh `import type`): `features/*` là domain nên không import `context/`. — `Áp dụng khi: structure, test`
- Vị trí file: rule nghiệp vụ → `option-set/<domain>/`, element + helper DOM → `option-types/<type>/`, test cạnh thứ nó test trong thư mục `tests/`. — `Áp dụng khi: structure`

## Vùng nóng / dễ vỡ (hotspots)
- `features/atc/` (`buildCartProperties`, `serializeOptionValue`): chuỗi ở đây **đi thẳng vào order**; đổi format là đổi dữ liệu merchant đọc. — `Áp dụng khi: logic`
- `context/create-context.ts`: nơi duy nhất đọc `window.Shopify` cho phần locale/currency; cờ `features.*` quyết định bật tính năng theo store. — `Áp dụng khi: logic, config`

## Bẫy tái diễn (pattern-level)
- **Format ngày bằng `Intl.DateTimeFormat` mà không ghim `calendar: 'gregory'`**: một số locale mặc định lịch khác (vd `th` → Phật lịch, `fa` → Jalali), nên chuỗi hiển thị/ghi order lệch so với giá trị ISO Gregorian đã lưu. Mọi chỗ dựng formatter cho ngày ISO phải ghim calendar, và nên có test `th`/`fa`. — `Áp dụng khi: logic`
- **Thêm một giá trị dùng chung cho field và cart property nhưng chỉ nối một nhánh** → ô input và order hiện ngôn ngữ/format khác nhau. Khi diff thêm field vào context, truy cả hai nhánh (`optionContext` và `CartPropertiesSource`). — `Áp dụng khi: logic`
- **Gate theo gói/cờ chỉ áp ở tầng render** (lọc `items` trong element) trong khi `optionConfigs`/`OptionSetState` vẫn dựng từ `items` gốc → validation, price addon, `buildCartProperties`, condition vẫn chạy trên Option đã bị ẩn (required không điền được → không Add to Cart; default value vẫn cộng tiền/ghi property). Gate phải áp ở nguồn, trước khi dựng Instance/state; test phải kiểm state/cart chứ không chỉ DOM. — `Áp dụng khi: logic, ui`
- **Tên feature/flag là `string` thô** (vd `isFeatureAllowed('OPTION_GROUP')`): gõ sai thì lặng lẽ không chặn, và quy ước "set/map rỗng = cho phép tất cả" biến tier lỡ để rỗng thành mở hết. Ưu tiên union/`as const` + kiểm `satisfies`. — `Áp dụng khi: logic, config`
- **Logic gói trong runtime cần spec đi kèm**: `option-core` ("Runtime SHALL KHÔNG chứa logic gói") và `plan-gating` ("cơ chế gate… ở change riêng") đang nói ngược code; diff thêm gate phải kèm OpenSpec change/delta, và quyết định sản phẩm (vd group thuộc gói nào) phải khớp spec archive hoặc ghi đè rõ ràng. — `Áp dụng khi: logic, config`
- Diff có lượt Prettier reformat lẫn với thay đổi logic (nhiều file ở HEAD chưa từng được format) → hunk nhiễu; dùng `git diff -w` để thấy thay đổi thật và đừng raise hunk chỉ đổi format. — `Áp dụng khi: always`

## Trọng tâm cần soi kỹ nhất
- Mọi thay đổi chuỗi trong `features/atc/` → ảnh hưởng order, kiểm tra tương thích ngược khi tính năng (translation…) tắt: output phải y hệt V1.
- Đường đi của một giá trị cấu hình qua `InstanceContext` → `optionContext` / `CartPropertiesSource`: không nhánh nào bị bỏ sót.
- Element sau refactor: selector `data-optis-po-*` khớp template, listener add/remove đối xứng.

## Không áp dụng / bỏ qua (giảm nhiễu)
- Không có db / API endpoint / auth / webhook / external-call phía server trong repo này (storefront thuần; Storefront API chỉ qua `storefront/` + `metaobject/` loaders) — bỏ qua các section đó của `base.md`/`shopify-app.md` trừ khi diff thật sự thêm.
- Section Embedded frontend / Polaris / App Bridge của `shopify-app.md` không áp dụng (đây là theme extension, không phải Admin UI).
