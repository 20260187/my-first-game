# Week 11 실습

## 오늘 한 것
- PyInstaller 설치 및 빌드
- resource_path() 함수 추가
- --add-data 옵션으로 에셋 포함
- .exe 실행 확인

## resource_path() 를 써야 하는 이유
- 경로 불일치 문제 해결: 파이썬 파일(`.py`)을 개발 환경(Thonny)에서 실행할 때는 현재 작업 디렉터리가 소스코드 폴더로 유지되어 상대 경로(`assets/...`)가 올바르게 인식됩니다. 그러나 `--onefile` 옵션으로 빌드된 실행 파일(`.exe`)은 실행 시 `AppData/Temp/_MEIxxxxx`라는 시스템 임시 폴더에 압축을 풀고 구동되므로, 일반 상대 경로를 사용하면 이미지나 사운드 에셋을 찾지 못하는 경로 깨짐 현상(`FileNotFoundError`)이 발생합니다.
- 분기 처리의 필요성: PyInstaller는 임시 폴더 경로를 `sys._MEIPASS`라는 변수에 저장합니다. 따라서 `resource_path()` 함수를 사용해 `sys._MEIPASS` 변수가 존재하면 임시 폴더를 base 경로로 잡고, 없으면 일반 개발 환경 경로(`__file__`)를 base로 잡도록 동적 분기 처리를 해 주어야 개발 환경과 배포 환경 모두에서 에셋이 정상적으로 로드됩니다.

## 빌드 명령어
### 1. 기본 단일 파일 빌드 (테스트용)
```bash
pyinstaller --onefile game.py