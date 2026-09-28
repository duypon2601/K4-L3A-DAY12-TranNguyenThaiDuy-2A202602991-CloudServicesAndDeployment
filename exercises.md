# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng placeholder "Câu trả lời của bạn" bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Trần Nguyễn Thái Duy  Mã học viên: 2A202602991

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Lúc deploy lên Railway, service `agent` được tạo trước, biến môi trường set
> sau. Nếu `agent_api_key` có mặc định `"changeme"` thì bản deploy đầu tiên vẫn
> chạy bình thường, `/health` xanh, và `/ask` mở cho bất kỳ ai gửi header
> `X-API-Key: changeme` — giá trị này ai đọc code trên GitHub (repo public) cũng
> biết. Người ta dùng nó gọi LLM bằng tiền của mình, và mình không hề biết vì
> mọi thứ trông "healthy". Với fail fast, thiếu biến là process chết ngay:
>
> ```
> pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
> agent_api_key
>   Field required [type=missing, input_value={}, input_type=dict]
> ```
>
> Health check trên Railway fail → deploy bị đánh dấu lỗi → mình phải vào sửa
> trước khi service nhận được request nào. Lỗi cấu hình lộ ra lúc deploy thay vì
> lúc bị lạm dụng.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log thu được khi gọi `/ask` (chạy local, user `sv-duy`):
>
> ```json
> {"event": "ask_completed", "level": "info", "timestamp": "2026-09-28T16:05:33.910066+00:00", "user_id": "sv-duy", "tokens_in": 54, "tokens_out": 54, "cost_usd": 4.05e-05}
> ```
>
> 1. **Lọc và tổng hợp theo trường.** Railway tự parse JSON này thành các
>    field (log trên dashboard hiện `event="ask_completed" user_id="cp5-test"
>    cost_usd=0.00002145`), nên mình lọc được theo `user_id` hoặc cộng
>    `cost_usd` theo user/ngày để đối chiếu với cost guard. Với
>    `print("đã trả lời xong")` thì không biết ai hỏi, tốn bao nhiêu.
> 2. **Cảnh báo và ghép log theo thời gian.** Có `timestamp` UTC và `level`
>    nên có thể đặt alert kiểu "tokens_out trung bình tăng đột biến" hay
>    "tỉ lệ event lỗi > 5% trong 5 phút", và ghép log của 3 container theo thời
>    gian. Chuỗi text tự do thì phải viết regex riêng cho từng câu và dễ vỡ khi
>    ai đó sửa câu chữ.

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
| 1 stage (bản đầu) | ... MB |
| Multi-stage | ... MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Số đo thật trên máy mình (`docker image inspect ... --format '{{.Size}}'`):
>
> | Bản | Dung lượng |
> |-----|-----------|
> | 1 stage (`python:3.11`, `COPY . .`) | 1.73 GB (1 732 422 394 B) |
> | Multi-stage (`python:3.11-slim`) | 335 MB (335 293 121 B) |
>
> Chênh ~1.4 GB, gần như toàn bộ đến từ **base image**: `python:3.11` bản đầy
> đủ dựa trên Debian có sẵn gcc, make, header `-dev`, git, curl, man page... để
> build được extension C. `docker history agent:single` cho thấy layer
> `pip install` chỉ 95 MB, phần còn lại là các layer của base. App mình toàn
> wheel đã build sẵn nên không cần compiler lúc chạy. Ngoài ra bản 1 stage
> `COPY . .` kéo theo cả thứ không cần (test, tài liệu), còn bản multi-stage chỉ
> copy `/opt/venv`, `app/`, `utils/` và pip chạy với `--no-cache-dir` nên không
> để lại cache của pip trong image.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Mình sửa một ký tự trong `app/main.py` rồi `docker build --progress=plain`:
>
> - **Dùng lại cache:** `FROM python:3.11-slim`, `WORKDIR`, `RUN python -m venv`,
>   `COPY requirements.txt`, `RUN pip install` (bước tốn thời gian nhất),
>   `COPY --from=builder /opt/venv`, `RUN useradd`.
> - **Chạy lại:** `COPY app/ app/` (hash file đổi) và mọi layer sau nó —
>   `COPY utils/ utils/`. Cả build mất vài giây.
>
> Nếu đặt `COPY . .` trước `RUN pip install` thì layer `COPY` đổi hash mỗi lần
> sửa bất kỳ file nào, kéo theo `pip install` chạy lại từ đầu (tải và cài lại
> ~30 package) dù `requirements.txt` không đổi. Build từ vài giây thành cả phút,
> CI và `railway up` cũng chậm theo.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện: (1) code có lỗ hổng, ví dụ một thư viện parse input bị RCE
> hoặc mình lỡ gọi `subprocess` với chuỗi người dùng gửi → (2) kẻ tấn công chạy
> được lệnh shell trong container với quyền của process uvicorn → (3) nếu process
> là **root (UID 0)**, họ ghi được mọi file trong container, cài tool, và vì UID 0
> trong container chính là UID 0 trên host kernel (không có user namespace),
> bất kỳ lối thoát nào — volume mount thư mục host, `/var/run/docker.sock` bị
> mount nhầm, container `--privileged`, hay một lỗ hổng kernel/runc — đều cho
> họ **root trên host**.
>
> `USER appuser` (UID 1000) cắt chuỗi ở bước 3: shell họ có được chỉ là user
> thường, không ghi được vào `/usr`, `/etc`, không cài package, file host mount
> vào thuộc root thì không sửa được, và một lỗ hổng thoát container sẽ ra host
> với UID 1000 chứ không phải root. Code app chỉ cần đọc `app/` và mở socket
> cổng > 1024 nên không mất gì khi bỏ root.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> **Tối đa 20 request trong 2 giây.** Với fixed window reset ở giây :00, bộ
> đếm chỉ biết "phút này đã bao nhiêu". Người dùng gửi 10 request lúc
> 10:00:59 (phút 10:00 đủ 10, hợp lệ), rồi bộ đếm về 0 lúc 10:01:00, gửi tiếp
> 10 request lúc 10:01:00–10:01:01 (phút 10:01 cũng đủ 10, hợp lệ) → 20 request
> trong ~2 giây, gấp đôi hạn mức.
>
> Sliding window của mình lưu timestamp từng request trong ZSET và đếm 60 giây
> *gần nhất* tính từ lúc request đến. Lúc 10:01:01, 10 request lúc 10:00:59 vẫn
> nằm trong cửa sổ nên request thứ 11 bị 429. Trên bản deploy mình gọi 15 lần
> liền và nhận đúng `200` × 9 rồi `429` × 6 (1 lượt đã dùng ở lần gọi trước).

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> **Rate limit** giới hạn *số lượng request trong một khoảng thời gian ngắn*
> (10/phút, cửa sổ 60 s, trả 429, tự hồi sau 1 phút) — chống spam và bảo vệ
> service khỏi bị dồn tải. **Cost guard** giới hạn *tổng tiền* một user tiêu
> trong tháng (10 USD, trả 402, chỉ hồi sang tháng sau) — chống hóa đơn LLM
> vượt ngân sách. Một cái đếm lượt, một cái đếm tiền.
>
> - *Rate limit cho qua, cost guard chặn:* một user gửi đều 5 request/phút —
>   không bao giờ chạm 10/phút — nhưng mỗi câu hỏi dán kèm tài liệu dài hàng
>   chục nghìn token. Sau vài ngày tổng `cost:<user>:2026-09` vượt 10 USD →
>   cost guard trả 402 dù tốc độ gọi rất bình thường.
> - *Cost guard cho qua, rate limit chặn:* một script lỗi gọi `/ask` 15 lần
>   trong 1 giây với câu hỏi "test" (~0.00002 USD/lần). Tổng tiền không đáng kể
>   nhưng từ request thứ 11 bị 429 — đúng như mình thấy khi test bản deploy.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Giả sử một endpoint duy nhất vừa là liveness vừa là readiness và có ping
> Redis, cụm 3 container sau load balancer:
>
> 1. **t = 0 s:** Redis mất kết nối. Cả 3 container cùng lúc trả 503 ở endpoint
>    đó (vì chúng dùng chung một Redis).
> 2. **Vài giây sau:** readiness fail → load balancer rút cả 3 khỏi pool. Không
>    còn instance nào nhận traffic → người dùng nhận 502/503 ngay cả với request
>    không cần Redis.
> 3. **Sau N lần liveness fail liên tiếp** (vd. 3 × 10 s): orchestrator coi
>    container là "chết" và **restart** cả 3. Container không có lỗi gì —
>    restart không sửa được Redis.
> 4. **Trong lúc restart:** container mới khởi động, lại ping Redis vẫn đang
>    hỏng → fail tiếp → vòng restart lặp lại (restart loop / CrashLoopBackOff),
>    có thể chạm `restartPolicyMaxRetries` và bị dừng hẳn.
> 5. **t = 30 s:** Redis sống lại, nhưng container đang giữa chừng khởi động
>    hoặc bị backoff → dịch vụ hồi phục chậm hơn nhiều so với 30 s, và các
>    request đang xử lý dở đã bị cắt ngang khi restart.
>
> Tách ra thì `/health` (không đụng Redis) vẫn 200 nên không ai restart
> container, còn `/ready` trả 503 chỉ tạm rút instance khỏi pool rồi tự nhận lại
> traffic ngay khi Redis về — sự cố 30 s chỉ kéo dài đúng 30 s.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Mình chạy 3 bản `agent` (`--scale agent=3`, mỗi bản một cổng host ngẫu nhiên
> vì cổng `8000:8000` cố định không cho 3 container cùng bind) và gọi `/ask`
> xoay vòng qua từng container với cùng `X-User-Id: sv-scale`:
>
> ```
> d12scale-agent-1 -> history_length = 0
> d12scale-agent-2 -> history_length = 2
> d12scale-agent-3 -> history_length = 4
> d12scale-agent-1 -> history_length = 6
> d12scale-agent-2 -> history_length = 8
> d12scale-agent-3 -> history_length = 10
> ```
>
> Con số tăng đều 2 mỗi lượt (1 câu hỏi + 1 câu trả lời) bất kể container nào
> xử lý, vì cả 3 đọc/ghi cùng một list trong Redis.
>
> Nếu lưu trong dict Python, mỗi process có dict riêng nên sẽ thấy
> `0, 0, 0, 2, 2, 2`: mỗi container chỉ nhớ những lượt *nó* đã xử lý. Với load
> balancer chia ngẫu nhiên, con số nhảy lung tung (vd. `0, 2, 0, 4, 2...`),
> chatbot "quên" câu trước tùy request rơi vào đâu, và mất sạch khi container
> restart hoặc Railway deploy bản mới.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> **Lỗi:** chạy `railway init --name day12-customer-support-agent` thì CLI
> báo:
>
> ```
> Your trial has expired. Please select a plan to continue using Railway.
> No linked project found. Run railway link to connect to a project
> ```
>
> Sau đó lệnh tiếp theo lại báo `Unauthorized. Please run railway login again.`
>
> **Tìm nguyên nhân:** `railway whoami` và `railway list` cho thấy mình đang
> đăng nhập vào workspace cũ đã dùng hết trial. Lỗi nằm ở tài khoản chứ không
> phải code, nên build chưa hề được chạy.
>
> **Sửa:** `railway login` lại vào workspace `duypon2601's Projects` còn hạn
> (dashboard hiện "30 days or $5.00 left"), `railway init` thành công, rồi
> `railway add --database redis`, tạo service `agent` với biến môi trường, và
> `railway up`.
>
> Trước khi `railway up` mình cũng xử lý trước một lỗi `$PORT`: `railway.toml`
> ban đầu có `startCommand = "uvicorn ... --port $PORT"`. Với builder Dockerfile,
> Railway chạy start command ở exec form (không qua shell) nên `$PORT` không
> được thay. Mình xóa `startCommand` để dùng `CMD` shell-form trong Dockerfile;
> log deploy xác nhận `Uvicorn running on http://0.0.0.0:8080` — đúng cổng
> Railway gán — và `/health`, `/ready` đều trả 200.
