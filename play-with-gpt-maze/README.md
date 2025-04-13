# Run
```
$ jupyter lab
```

## stable-baseline3

stable-baselines3[extra]는 강화 학습(Reinforcement Learning, RL)을 위한 Python 라이브러리인 Stable-Baselines3의 확장 버전입니다. 이 패키지는 강화 학습 알고리즘을 쉽게 구현하고 실험할 수 있도록 설계되었습니다. [extra]는 추가적인 의존성을 포함하는 옵션입니다.

### Stable-Baselines3란?
Stable-Baselines3는 강화 학습 알고리즘의 구현체로, TensorFlow 기반의 Stable-Baselines를 PyTorch로 재작성한 라이브러리입니다. 강화 학습 알고리즘을 연구하거나 실험할 때 널리 사용됩니다.

주요 알고리즘:
- A2C (Advantage Actor-Critic)
- PPO (Proximal Policy Optimization)
- DQN (Deep Q-Network)
- SAC (Soft Actor-Critic)
- TD3 (Twin Delayed Deep Deterministic Policy Gradient)

### [extra] 옵션의 의미
stable-baselines3[extra]는 기본 패키지 외에 추가적인 의존성을 설치합니다. 이 옵션은 강화 학습 실험에 필요한 추가 도구를 포함합니다. 주요 추가 의존성은 다음과 같습니다:

- opencv-python:
환경에서 이미지를 처리하거나 시각화할 때 사용됩니다.
예: 게임 환경에서 화면 캡처 및 처리.

- matplotlib:
학습 결과를 시각화하거나 그래프를 그릴 때 사용됩니다.

- pandas:
데이터 분석 및 결과 저장에 사용됩니다.

- atari-py 및 ale-py:
Atari 환경을 실행하기 위한 패키지입니다. OpenAI Gym의 Atari 환경을 사용할 때 필요합니다.

- pytest:
테스트를 실행하기 위한 도구입니다.

### 왜 필요한가?
- 강화 학습 실험을 진행할 때, 환경 시뮬레이션, 데이터 시각화, 이미지 처리 등이 필수적입니다.
- [extra] 옵션을 사용하면 이러한 작업에 필요한 추가 패키지를 한 번에 설치할 수 있어 편리합니다.
- 특히, OpenAI Gym과 같은 강화 학습 환경을 사용할 때 유용합니다.


## gym

gym은 OpenAI에서 개발한 강화 학습(Reinforcement Learning) 환경을 제공하는 라이브러리입니다. 강화 학습 알고리즘을 실험하고 평가하기 위한 다양한 시뮬레이션 환경을 제공합니다.

### gym의 주요 특징

강화 학습 환경 제공:
- gym은 다양한 강화 학습 환경을 제공합니다. 예를 들어:
    - 클래식 제어 문제: CartPole, MountainCar, Pendulum 등.
    - 로봇 시뮬레이션: MuJoCo, Robotics 환경.
    - 게임 환경: Atari 게임(예: Pong, Breakout).
    - 보드 게임: 체스, 바둑 등.

표준화된 인터페이스:
- 모든 환경은 동일한 API를 사용하므로, 알고리즘을 쉽게 테스트하고 비교할 수 있습니다.
- 주요 메서드:
    - env.reset(): 환경 초기화.
    - env.step(action): 행동을 수행하고 다음 상태, 보상, 종료 여부 등을 반환.
    - env.render(): 환경 시각화.

확장 가능성:
- 사용자가 직접 환경을 정의하고 추가할 수 있습니다.

강화 학습 알고리즘 실험:
- gym은 강화 학습 알고리즘을 실험하고 평가하기 위한 표준 도구로 널리 사용됩니다.

### 왜 필요한가?
- 강화 학습 알고리즘을 개발하거나 실험하려면 환경이 필요합니다.
- gym은 다양한 환경을 제공하므로, 알고리즘의 성능을 쉽게 비교하고 평가할 수 있습니다.
- Stable-Baselines3와 같은 라이브러리와 함께 사용하면 강화 학습 실험을 더 쉽게 진행할 수 있습니다.