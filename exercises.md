# Phiếu Phản Ánh — K3 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay từng dòng trả lời mẫu `Câu trả lời của bạn` ở mỗi
> câu hỏi bằng câu trả lời thật. `grade.py` đếm số câu đã trả lời (15 điểm
> cho 10 câu).
>
> Họ và tên: Trần Công Chiến  Mã học viên: 2A202601053

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Tình huống: tôi deploy lên cloud mà quên set `AGENT_API_KEY` trong dashboard.
> Vì trường này không có mặc định, app ném `ValidationError: agent_api_key
> Field required` ngay lúc khởi động → health check fail → tôi thấy lỗi trong
> log deploy ngay trước khi có traffic thật. Nếu để mặc định `"changeme"`, app
> vẫn khởi động "bình thường", bot quét internet tìm thấy URL công khai rồi gọi
> API bằng khóa đó → tôi phát hiện ra chỉ khi hóa đơn LLM tăng vùn vụt. Nói cách
> khác: không mặc định = lỗi lộ ra ngay lúc tôi còn đang nhìn màn hình; có mặc
> định = lỗi lộ ra khi tôi đã rời màn hình.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log thật tôi thu được từ `log_event("ask_completed", ...)`:
>
> `{"event": "ask_completed", "level": "info", "timestamp": "2026-08-10T04:03:56.926172+00:00", "user_id": "sv01", "tokens_in": 45, "tokens_out": 120, "cost_usd": 0.00021}`
>
> Hai việc làm được với dòng log này mà `print()` không làm được:
> 1. **Thống kê/tổng hợp bằng máy:** vì dữ liệu có cấu trúc (trường `user_id`,
>    `cost_usd`, `tokens_in`), tôi lọc được "user nào tiêu nhiều tiền nhất hôm
>    nay" hoặc cộng dồn chi phí theo user bằng `grep`/`jq` hay công cụ log
>    aggregator (Datadog, CloudWatch...) — `print("đã trả lời xong")` chỉ là một
>    chuỗi văn bản vô nghĩa cho máy.
> 2. **Cảnh báo tự động (alerting):** tôi đặt ngưỡng — `cost_usd` vượt mức, hoặc
>    tỷ lệ lỗi trong 5 phút quá cao — để hệ thống tự cảnh báo. JSON một dòng là
>    một log nguyên vẹn; nếu xuống dòng thì cloud gom nhầm thành nhiều mảnh và
>    không truy vấn được.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1.7 GB |
| Multi-stage | 270 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Số đo thật khi build trên máy tôi: `agent:single` (1 stage, base `python:3.11`
> đầy đủ) = **1.7 GB**; `day12-agent:prod` (multi-stage) = **270 MB** — chênh
> ~1.4 GB. Phần chênh gồm: base image không-slim (đầy đủ build toolchain như
> `gcc`, `binutils`, các header `*.h` của C), pip cache và `__pycache__` còn
> sót. Multi-stage cắt nó bằng cách:
> stage `builder` cài dependency (nơi compiler được dùng), rồi stage `runtime`
> chỉ `COPY --from=builder /install /usr/local` — tức chỉ mang sang thư mục kết
> quả của `pip install`, không mang theo compiler. Image nhỏ = deploy nhanh hơn,
> và bề mặt tấn công nhỏ hơn.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Dockerfile của tôi có thứ tự: `COPY requirements.txt .` → `RUN pip install
> --prefix=/install ...` → `COPY . .`. Sửa một ký tự trong `app/main.py`:
> - **Dùng lại từ cache:** layer `COPY requirements.txt .` và `RUN pip install`
>   (vì `requirements.txt` không đổi).
> - **Phải chạy lại:** layer `COPY . .` (toàn bộ source thay đổi) và các layer
>   phía sau ở stage runtime (`COPY --from=builder /app /app`).
>
> Nếu đặt `COPY . .` TRƯỚC `RUN pip install`, thì bất kỳ lần sửa code nào cũng
> làm thay đổi layer COPY → Docker hủy cache toàn bộ từ đó trở đi → `pip install`
> phải cài lại hết thư viện. Mỗi lần sửa một dấu phẩy là vài phút build. Đặt
> `requirements.txt` + install trước là tận dụng cache đúng cách.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện: (1) có một lỗ hổng trong code Python — ví dụ đọc file theo
> đường dẫn lấy từ input, hoặc RCE qua một thư viện xử lý ảnh — kẻ tấn công
> chạy được lệnh bên trong container. (2) Nếu process chạy với uid 0 (root),
> kẻ đó đã có **root trong container**. (3) Từ root trong container, kết hợp
> với misconfiguration (mount `docker.sock`, chạy `privileged`, capability
> `SYS_ADMIN`) hoặc một kernel exploit, kẻ tấn công trèo lên **root trên host** —
> toàn bộ máy chủ.
>
> Lệnh `USER appuser` (uid 10001) cắt chuỗi ngay tại bước (2): process chỉ chạy
> với quyền của user thường, không ghi được file hệ thống, không có các capability
> mạnh. Dù kẻ tấn công có thoát khỏi container thì cũng không phải root trên host.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Tối đa **20 request trong 2 giây**. Cách đạt: gửi 10 request lúc cuối phút
> (ví dụ 10:00:59 — vẫn thuộc phút 10:00, chưa đủ 10 để bị chặn), sau đó chờ
> bộ đếm reset lúc sang giây 00, rồi gửi thêm 10 request nữa (10:01:00 — thuộc
> phút 10:01). Tổng cộng 20 request trong ~2 giây mà mỗi phút vẫn đúng hạn mức
> 10. Sliding window chặn kẽ hở này: nó đếm số request trong 60 giây **gần
> nhất** (`zremrangebyscore` vứt request ra khỏi cửa sổ), nên 20 request đó đều
> nằm trong cửa sổ trượt → bị trả 429.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit giới hạn **số lượng request** trong một khoảng thời gian; cost guard
> giới hạn **số tiền** một user tiêu trong tháng. Chúng không thay thế nhau.
>
> - **Rate limit cho qua, cost guard chặn:** user gửi đủ 10 request/phút (dưới
>   hạn mức), nhưng mỗi request kèm prompt rất dài (~50.000 token) → chi phí mỗi
>   request cao → cộng dồn chạm ngân sách tháng → `CostGuard.check` trả **402**.
> - **Cost guard cho qua, rate limit chặn:** user còn ngân sách (mới dùng vài
>   xu), nhưng gửi 50 request trong 10 giây → vượt 10/phút → `RateLimiter.check`
>   trả **429**.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Thứ tự sự kiện với cụm 3 container:
> 1. Redis mất kết nối → endpoint gộp (đang kiểm tra Redis) trả **503** ở cả
>    3 container → orchestrator coi cả 3 **unhealthy**.
> 2. Vì `/health` là liveness probe, orchestrator **restart cả 3 container cùng
>    lúc** (không phải ngừng gửi traffic).
> 3. Trong lúc restart, **không còn container nào phục vụ** → user nhận lỗi.
> 4. Khi Redis quay lại, cũng chưa chắc có instance nào sẵn sàng ngay → sự cố
>    nhỏ (Redis nghẽn 30 giây) thành sự cố toàn hệ thống.
>
> Tách riêng thì khác: `/health` chỉ hỏi "process còn sống?" (không đụng Redis),
> `/ready` mới hỏi "nhận traffic được chưa?" → khi Redis chết, load balancer chỉ
> **ngừng gửi request** tới instance báo 503, không restart → Redis hồi phục là
> instance tự quay lại phục vụ.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Khi lịch sử nằm trong Redis (của tôi: `lrange history:<user> 0 -1`), mọi
> container đọc/ghi cùng một key nên `history_length` **tăng dần đều** (0, 1, 2,
> 3, ...) dù request này rơi vào container A hay B. Còn nếu lưu trong dict Python
> trong RAM: mỗi container có một dict riêng, và load balancer chia request
> round-robin → request 1, 2, 3 vào container A (history_length tăng 0→1→2), rồi
> request 4 rơi vào container B mới khởi động (dict trống) → `history_length` quay
> về 0 → agent "mất trí nhớ" ngẫu nhiên, con số không đơn điệu. Đó chính là lý do
> state phải ra khỏi process.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> ⚠️ *(Sẽ cập nhật sau khi deploy thật — tôi chưa xong bước này.)* Quy trình chẩn
> đoán tôi sẽ dùng nếu gặp lỗi: mở log trên dashboard platform rồi kiểm tra theo
> thứ tự — (1) app có đọc `$PORT` không (nếu cố định 8000 thì health check
> timeout khi platform gán cổng khác); (2) `REDIS_URL` trên cloud có trỏ đúng
> instance Redis không (nếu sai thì `/ready` trả 503); (3) app có bind
> `127.0.0.1` thay vì `0.0.0.0` không. Khi có lỗi thực tế, tôi sẽ ghi lại thông
> báo cụ thể vào đây.
