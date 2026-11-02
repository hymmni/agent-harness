# Docker 개발 환경

컨테이너는 리포지토리 전체를 `/workspace`에 bind-mount 합니다. 컨테이너 안에서 코드를 고치는
게 아니라, 평소처럼 호스트(VSCode 등)에서 코드를 고치면 컨테이너에 바로 반영됩니다. **코드를
고쳐도 이미지 재빌드는 필요 없습니다.** `requirements.txt`를 바꿨을 때만 재빌드하면 됩니다.

## 0. 최초 1회 준비

```bash
cp .env.example .env
```

## 1. 빌드 & 실행 (CPU)

```bash
docker compose build
docker compose run --rm dev bash
```

## 2. GPU 있는 학습 서버에서 실행할 때

서버에 [NVIDIA driver](https://www.nvidia.com/Download/index.aspx) +
[nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)이 설치되어
있어야 합니다.

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm dev bash
```

## 3. VS Code로 작업할 때 (Dev Containers)

1. [Dev Containers 확장](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   설치
2. `Cmd/Ctrl+Shift+P` → `Dev Containers: Reopen in Container`

### 왜 non-root `dev` 사용자로 도는가

non-root는 마운트된 파일이 root 소유가 되는 것을 막습니다. `.devcontainer/devcontainer.json`은
`common-utils` feature로 만든 `dev` 사용자로 돌고, `updateRemoteUserUID: true`가 컨테이너 시작
시 그 사용자의 UID/GID를 호스트 사용자에 맞춰줍니다.

## 4. 에이전트와 함께 쓸 때

에이전트는 컨테이너 밖에서 실행하고 코드 실행은 `docker compose exec dev <명령>`으로 합니다.
먼저 컨테이너를 띄워 두세요.

```bash
docker compose up -d dev
docker compose exec dev python3 train.py
```

## 5. GUI 쓰기

호스트(Linux)에서 컨테이너의 X11 접근을 한 번 허용해야 합니다:

```bash
xhost +local:docker
```

그 다음 평소처럼 `docker compose run`하면 `DISPLAY`가 자동으로 전달됩니다.

## 6. 새 패키지가 필요할 때

컨테이너 안에서 바로 `pip install <패키지>`를 해도 그 컨테이너가 살아있는 동안만 유효합니다.
계속 쓸 패키지는 `requirements.txt`에 버전을 명시해서 추가한 뒤 `docker compose build`로
재빌드하세요.
