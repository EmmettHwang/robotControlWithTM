
---

## 📄 README.md (프로젝트 최종 문서)

# 🤖 Humanoid AI Intelligence Control System

본 프로젝트는 **TensorFlow Lite**와 **OpenCV**를 활용하여 휴머노이드를 지능적으로 제어하는 시스템입니다. 카메라를 통해 사물(사람, 로봇, 생활용품)을 인식하고, 지정된 모션 시퀀스를 로봇에 전송합니다.

---
## 🧠 1. AI Model: TensorFlow Lite (TFLite)

본 프로젝트는 실시간 객체 인식을 위해 무거운 정밀 모델 대신 **TensorFlow Lite** 엔진을 채택하였습니다.

### 1. 왜 TFLite인가?
* **경량화 (Lightweight)**: 일반적인 TensorFlow 모델(.pb, .h5)에 비해 용량이 매우 작아 로봇 제어용 PC나 임베디드 보드에서 메모리 점유율이 낮습니다.
* **실시간성 (Real-time Performance)**: 모델 최적화를 통해 낮은 지연 시간(Low Latency)으로 추론이 가능하여, 초당 수십 프레임의 영상을 처리하며 로봇에게 즉각적인 명령을 내릴 수 있습니다.
* **이식성 (Portability)**: Python 환경뿐만 아니라 안드로이드, iOS, 마이크로컨트롤러 등 다양한 플랫폼으로의 확장이 용이합니다.

### 2. 모델 추론 프로세스 (Inference Flow)
시스템 내에서 TFLite 모델은 다음과 같은 단계를 거쳐 로봇의 동작을 결정합니다.

1.  **전처리 (Pre-processing)**: 카메라 프레임을 모델 입력 규격인 `224x224` 크기로 리사이즈하고, 데이터를 `-1.0 ~ 1.0` 범위로 정규화합니다.
2.  **해석기 호출 (Interpreter Invoke)**: `Interpreter`를 통해 모델을 로드하고, 입력 텐서(Input Tensor)에 영상 데이터를 주입한 뒤 연산을 수행합니다.
3.  **결과 분석 (Post-processing)**: 출력된 확률 배열에서 가장 높은 값(Argmax)을 찾아 물체의 라벨(사람, 로봇, 생활용품)과 정확도(Confidence)를 추출합니다.

### 3. 기술적 사양
* **입력 크기**: 224 x 224 (RGB)
* **최적화 방식**: Float32 (Unquantized) - 인식 정확도를 우선시함
* **추론 임계값**: 0.85 (85% 이상의 확신이 있을 때만 로봇 동작 수행)
* 
## 🛠️ 2. 개발 환경 구축 (Environment Setup)

TensorFlow와 하드웨어 제어 라이브러리의 안정성을 위해 반드시 **Python 3.11** 환경을 사용해야 합니다.

### **가상환경 생성 및 필수 라이브러리 설치**
미니콘다(Miniconda) 터미널에서 아래 명령어를 순서대로 입력하세요.

```bash
# 1) Python 3.11 기반 가상환경 생성
conda create -n ObjectCam python=3.11 -y

# 2) 가상환경 활성화
conda activate ObjectCam

# 3) 필수 패키지 설치
pip install tensorflow opencv-python pillow pyserial
(또는 pip install -r requirements.txt)
```

### **VS Code 설정**
1. `Ctrl + Shift + P` -> `Python: Select Interpreter` 선택
2. 목록에서 `Python 3.11.x ('ObjectCam')`를 선택하여 에디터와 연결합니다.

---

## ⚙️ 3. 시스템 구성 및 파일 구조

* `main.py`: 전체 시스템 실행 소스 코드
* `model_unquantized.tflite`: 티쳐블 머신으로 학습된 AI 모델 파일
* `labels.txt`: 학습된 클래스 이름 (사람, 로봇, 생활용품 등)
* `config.ini`: 마지막으로 사용한 시리얼 포트 정보를 저장 (자동 생성)

---

## 🚀 4. 주요 기능 및 로직

### **A. 지능형 동작 시퀀스**
무분별한 명령 전송을 방지하고 로봇의 안정적인 동작을 위해 다음 시퀀스를 따릅니다.
1.  **객체 인식**: 85% 이상의 확률로 사물 감지 (이전 인식 결과와 다를 때만 실행).
2.  **메인 동작**: 해당 물체에 맞는 모션(19, 39, 84번 중 하나) 전송.
3.  **1단계 대기**: 메인 동작 후 **7초간** 화면 안내와 함께 대기.
4.  **기본 복귀**: 7초 후 자동으로 **1번(기본 자세)** 모션 전송.
5.  **2단계 대기**: 복귀 후 **3초간** 추가 대기 후 다시 감지 모드로 전환.

### **B. 사용자 인터페이스 (GUI)**
* **실시간 안내**: 초기화 1~4단계(포트, 모델, 엔진, 카메라)를 진행바와 함께 실시간 표시.
* **수동 제어 버튼**: 화면 하단 버튼 클릭으로 인사(19), 손흔들기(18), 챔피온(17) 즉시 실행 가능.
* **호버링 효과**: 버튼 위에 마우스를 올리면 커서가 **손가락 모양**으로 변경되어 직관적인 조작 지원.
* **종료 버튼**: 화면 상단 우측의 [종료] 버튼 클릭 시 시리얼 포트를 안전하게 닫고 프로그램 종료.

---

## 📡 5. 하드웨어 통신 규격

* **Baudrate**: 115200 bps
* **Protocol**: 15-Byte Packet 구조
* **Checksum**: 6번~13번 인덱스 바이트 합산 연산 (`& 0xFF`) 적용

---

## ⚠️ 주의사항
1.  **카메라 초기화**: 4번 단계(카메라 활성화)는 하드웨어 응답 속도에 따라 약 2~3초 정도 소요될 수 있습니다.
2.  **포트 중복 사용**: 아두이노 시리얼 모니터 등 다른 프로그램이 COM 포트를 점유 중이면 실행되지 않습니다. (PermissionError 발생 시 확인 필요)

---
<img width="443" height="500" alt="image" src="https://github.com/user-attachments/assets/8921698a-a96f-4832-bb48-28d0c7df98ee" />

<img width="410" height="553" alt="image" src="https://github.com/user-attachments/assets/87cdf029-9636-468d-9a48-6625b46d1efd" />

https://youtube.com/shorts/v38ii_hiWxc?si=_PjQL4xd9vPc-Sj4
