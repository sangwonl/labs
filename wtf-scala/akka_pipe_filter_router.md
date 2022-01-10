---
marp: true
theme: gaia
---

# ![50%](https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/Akka_toolkit_logo.svg/1200px-Akka_toolkit_logo.svg.png)
#### 2018. 04. 26
###### Sangwon Lee

---

### Topic

- 파이프라인
  - 파이프-필터 패턴
  - 분배-취합 패턴
  - 라우팅 슬립 패턴
  - 라우터 패턴
  	- 풀 라우터
  	- 그룹 라우터
  	- ConsistentHasing 라우터

---

### 파이프라인

**파이프?** 한 프로세스(서)나 스레드가 결과를 다른 프로세스(서)나 스레드에게 전달해서 다음 처리를 맡기는 것.

**파이프라인?** 파이프로 여러 컴포넌트를 연결한 것. 특정 단계에서 독립적으로 처리할 수 있는 부분을 병렬로 수행할 수도 있음.

![200%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig02_alt.jpg)

---

#### 파이프-필터(Pipe-Filter) 패턴

- 시스템에서 단일 이벤트가 일련의 작업을 촉발할때
- 가령, 과속 탐지 카메라
  - 사진을 찍고
  - 속도를 측정하고
  - 사진에서 번호판을 추출하고

![200%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig01_alt.jpg)

---

```scala
case class Photo(
  license: String, speed: Int)
  
class SpeedFilter(minSpeed: Int, pipe: ActorRef)
    extends Actor {
  def receive = {
    case msg: Photo =>
      if (msg.speed > minSpeed)
        pipe ! msg
  }
}

class LicenseFilter(pipe: ActorRef) extends Actor {
  def receive = {
    case msg: Photo =>
      if (!msg.license.isEmpty)
        pipe ! msg
  }
}
```

---

```scala
// 속도 검사 필터에서 더 많은 메시지가 걸러진다고 가정하고,
// SpeedFilter --> LicenseFilter 순으로 메시지 파이프라이닝
val endProbe = TestProbe()
val licenseFilterRef = system.actorOf(
  Props(new LicenseFilter(endProbe.ref)))

val speedFilterRef = system.actorOf(
  Props(new SpeedFilter(50, licenseFilterRef)))

val msg = new Photo("123xyz", 60)
speedFilterRef ! msg
endProbe.expectMsg(msg)

speedFilterRef ! new Photo("", 60)
endProbe.expectNoMsg(1 second)

speedFilterRef ! new Photo("123xyz", 49)
endProbe.expectNoMsg(1 second)
```

---

#### 분배-취합(Scatter-Gather) 패턴

- 작업을 병렬로 실행하고 싶을때
- 두가지 케이스에 많이 활용
  - 같은 기능의 작업(경쟁 작업)을 분배하고 그 결과 중 하나만 취합
    - 예) 여러 정렬 알고리즘을 동시 실행, 그 중 가장 빠른 결과를 사용하고 나머지는 버림
  - 전체 작업을 여러개로 분할해서 분배하고 결과를 모두 취합
    - 예) 앞서, 과속 탐지 카메라의 속도와 번호판 인식을 병렬로 수행시킴

---

#### `경쟁 작업의 분배 및 취합`

_물품의 가격을 가져오기 위해 여러 공급사(supplier)에 가격을 요청하고 그 중에 가장 저렴한 가격을 Take._

![200%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig06_alt.jpg)

---

#### `작업을 분할하여 분배 및 취합 (1/3)`

_과속탐지기의 촬영 사진으로부터 시간과 속도를 추출하는 작업을 GetTime / GetSpeed 로 분할하여 처리하고 취합._

![60%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig07_alt.jpg) ![80%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig08_alt.jpg)

---

#### `작업을 분할하여 분배 및 취합 (2/3)`

**Scatter 구현** (RecipientList Actor)

![120%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig09_alt.jpg)

![120%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig10_alt.jpg)

---

```scala
val endProbe1 = TestProbe()
val endProbe2 = TestProbe()
val endProbe3 = TestProbe()
val list = Seq(
  endProbe1.ref,
  endProbe2.ref,
  endProbe3.ref)

val actorRef = system.actorOf(
  Props(new RecipientList(list)))

val msg = "message"
actorRef ! msg 
endProbe1.expectMsg(msg)
endProbe2.expectMsg(msg)
endProbe3.expectMsg(msg)

```

---

#### `작업을 분할하여 분배 및 취합 (3/3)`

**Gather 구현** (Aggregator Actor)

![200%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig11_alt.jpg)

---

```scala
class Aggregator(timeout: Duration, pipe: ActorRef)
    extends Actor {
  val messages = new ListBuffer[PhotoMessage]
  def receive = {
    case rcvMsg: PhotoMessage => {
      messages.find(_.id == rcvMsg.id) match {
        case Some(alreadyRcvMsg) => {
          val newCombinedMsg = new PhotoMessage(
            rcvMsg.id,
            rcvMsg.photo,
            rcvMsg.creationTime.orElse(alreadyRcvMsg.creationTime),
            rcvMsg.speed.orElse(alreadyRcvMsg.speed))
          pipe ! newCombinedMsg
          //cleanup message
          messages -= alreadyRcvMsg
       }
       case None => messages += rcvMsg
     }
   }
}
```

---

```scala
val endProbe = TestProbe()
val actorRef = system.actorOf(
  Props(new Aggregator(1 second, endProbe.ref)))

val photoStr = ImageProcessing.createPhotoString(
  new Date(), 60)

val msg1 = PhotoMessage("id1", photoStr,
  Some(new Date()),None)
actorRef ! msg1

val msg2 = PhotoMessage("id1", photoStr,
  None, Some(60))
actorRef ! msg2 

val combinedMsg = PhotoMessage("id1", photoStr,
  msg1.creationTime, msg2.speed)
endProbe.expectMsg(combinedMsg)
```

---

#### 라우팅 슬립(Routing Slip) 패턴

- 파이프-필터 패턴의 동적인 버전
- 작업의 흐름을
  - 전혀 다른 파이프-필터를 태우거나
  - 파이프라인의 특정 파이프부터 태우거나
- Router가 메시지가 처리될 Actor의 경로를 결정해서 routeSlip (Seq[ActorRef])에 담음
- routeSlip은 모든 메시지 포함됨
- 메시지를 처리하는 각 액터는 routeSlip의 액터 순서에 따라 다음 액터에게 메시지를 넘김

---

![200%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/08fig14_alt.jpg)

`slip` <span style="font-size: 15px;">노트북 파우치 처럼 밀어넣는 느낌의 주머니라고 생각하시면 됩니다. 환자가들어와서 나갈때까지 진료에 실수가 없도록 발생한 문서들을 차곡차곡 넣어두는 봉투라는 병원 용어로도 쓰인다고 하네요. routeSlip 은 어떤 여정을 담는 주머니. (feat. 리아)</span>

---

```scala
case class RouteSlipMessage(
  routeSlip: Seq[ActorRef],
  message: AnyRef)
  
trait RouteSlip {
  def sendMessageToNextTask(routeSlip: Seq[ActorRef],
      message: AnyRef): Unit = {
      
    val nextTask = routeSlip.head
    val newSlip = routeSlip.tail
    if (newSlip.isEmpty) {
      nextTask ! message
    } else {
      nextTask ! RouteSlipMessage(
        routeSlip = newSlip,
        message = message)
    }
  }
}
```

---

```scala
class PaintCar(color: String) extends Actor with RouteSlip {
  def receive = {
    case RouteSlipMessage(routeSlip, car: Car) => {
      sendMessageToNextTask(routeSlip, car.copy(color = color))
    }
  }
}
class AddNavigation() extends Actor with RouteSlip {
  def receive = {
    case RouteSlipMessage(routeSlip, car: Car) => {
      sendMessageToNextTask(routeSlip, car.copy(hasNavigation = true))
    }
  }
}
class AddParkingSensors() extends Actor with RouteSlip {
  def receive = {
    case RouteSlipMessage(routeSlip, car: Car) => {
      sendMessageToNextTask(routeSlip, car.copy(hasParkingSensors = true))
    }
  }
}
```

---

```scala
class SlipRouter(endStep: ActorRef) extends Actor with RouteSlip {
  val paintBlack = context.actorOf(
    Props(new PaintCar("black")), "paintBlack")
  val paintGray = context.actorOf(
    Props(new PaintCar("gray")), "paintGray")
  val addNavigation = context.actorOf(
    Props[AddNavigation], "navigation")
  val addParkingSensor = context.actorOf(
    Props[AddParkingSensors], "parkingSensors")
  def receive = {
    case order: Order => {
      val routeSlip = createRouteSlip(order.options) 
      sendMessageToNextTask(routeSlip, new Car)
    }
  }
  
  private def createRouteSlip...
}
```

---

```scala
private def createRouteSlip(
    options: Seq[CarOptions.Value]): Seq[ActorRef] = {
    
  val routeSlip = new ListBuffer[ActorRef]
  //car needs a color
  if (!options.contains(CarOptions.CAR_COLOR_GRAY)) {
    routeSlip += paintBlack
  }
  options.foreach {
    case CarOptions.CAR_COLOR_GRAY  => routeSlip += paintGray
    case CarOptions.NAVIGATION      => routeSlip += addNavigation
    case CarOptions.PARKING_SENSORS => routeSlip += addParkingSensor
    case other                      => //do nothing
  }
  routeSlip += endStep
  routeSlip
}
```

---

```scala
val probe = TestProbe()
val router = system.actorOf(
  Props(new SlipRouter(probe.ref)), "SlipRouter")
```

```scala
val minimalOrder = new Order(Seq())
router ! minimalOrder 

val defaultCar = new Car(color = "black", hasNavigation = false, hasParkingSensors = false)
probe.expectMsg(defaultCar)

val fullOrder = new Order(Seq(CarOptions.CAR_COLOR_GRAY, CarOptions.NAVIGATION, CarOptions.PARKING_SENSORS))
router ! fullOrder

val carWithAllOptions = new Car(color = "gray", hasNavigation = true, hasParkingSensors = true)
probe.expectMsg(carWithAllOptions)
```

---

#### 라우터 패턴

`라우터`

메시지를 어디로 보낼지 결정하는 녀석

`라우티`

라우터가 선택할 수 있는 작업(액터)

`라우팅`

메시지의 내용에 따라, 혹은 처리시간이 오래 걸리는 메시지를 병렬로 처리하기 위해, 혹은 라우터의 상태에 따라 메시지의 흐름을 결정하는 일

---

- 이전 챕터에서는 파이프-필터 / 분배-취합 / 라우팅슬립 등의 패턴으로 메시지의 흐름을 제어하는 방법을 익혔다면

- 이번 챕터는 수 많은 메시지를 처리할때 시스템의 성능을 높이는 방법. 즉, 로드 밸런싱을 위한 라우팅에 집중을 해봄

![130%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/09fig02_alt.jpg)

---
**내장라우터 종류**
|풀(Pool)|그룹(Group)|
|-|-|
|- 라우티를 관리|- 라우티를 안관리|
|- 라우티를 만드는 것부터 라우티 종료 시 목록에서 제거하는 것 까지 책임|- 라우티는 시스템에 의해 생성되며 그룹 라우터는 액터 선택을 사용해 라우티를 선택|
|- 라우티를 복구하는데 특별한 절차가 안필요|- 그룹 라우터는 라우티를 감시하지 않으므로 라우티 관리는 시스템의 다른 부분에서 구현해야함|
|- 단순해서 쉽게 쓸 수 있지만 라우팅 로직의 커스터마이징이 불가|- 라우티의 생명주기를 특별히 제어하고 싶을때 사용하기 좋음

--- 

**풀 라우터와 그룹 라우터의 액터 계층**

![110%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/09fig03_alt.jpg)

---

**아카에서 사용할 수 있는 라우터 목록**

**RoundRobinRoutingLogic**
<span style="font-size: 18px;">첫번째로 도착한 메시지를 첫번째 라우티, 두번째 메시지는 두번째 라우티, ...</span>

`Pool` RoundRobinPool
`Group` RoundRobinGroup
\
\
**SmallestMailboxRoutingLogic**
<span style="font-size: 18px;">라우티의 수신함을 검사해서 수신함에 가장 메시지가 적은 라우티를 선택. 액터 내부 기능을 이용하기 때문에 액터 참조를 이용하는 경우는 우편함의 길이를 알 수 없어서 그룹 라우터는 미존재.</span>

`Pool` SmallestMailboxPool
`Group` N/A

---

**BalancingRoutingLogic**
<span style="font-size: 18px;">유휴 상태인 라우티에 메시지를 분배. 이 라우터는 모든 라우티에 대해 우편함을 하나만 사용함. 특별한 디스패처를 사용함. 그래서 이것도 그룹은 없음. 또한, 이 라우터는 broadcast를 지원하지 않음. (왜?)</span>

`Pool` BalancingPool
`Group` N/A
\
\
**BroadcastRoutingLogic**
<span style="font-size: 18px;">받은 메시지를 모든 라우티에 전달.</span>

`Pool` BroadcastPool
`Group` BroadcastGroup

---

**ScatterGatherFirstCompletedRoutingLogic**
<span style="font-size: 18px;">메시지를 모든 라우티에 전달하고 최초로 돌아오는 응답을 요청한 객체에 돌려줌. 경쟁 작업의 분배-취합 패턴이라고 보면 됨.</span>

`Pool` ScatterGatherFirstCompletedPool
`Group` ScatterGatherFirstCompletedGroup
\
\
**ConsistentHashingRoutingLogic**
<span style="font-size: 18px;">메시지의 일관성 있는 해시값을 가지고 라우티를 선택. 여러 다른 메시지가 같은 라우티에 전달되어야 할때 사용.</span>

`Pool` ConsistentHashingPool
`Group` ConsistentHashingGroup

---

#### 풀 라우터와 그룹 라우터

앞선 예제인 과속탐지 시스템에서 차량 번호를 추출하는 GetLicense 액터를 라우티로 하여 `풀라우터`와 `그룹라우터`를 생성하고 이용해보자.

두 라우터 설정 모두 동적으로 라우티(액터)의 사이즈를 변경시키는 resize 라는 정책들이 있는데, 그 부분은 Skip.

---
##### 풀 라우터

_설정으로 풀라우터 생성_

```scala
val router = system.actorOf(
  FromConfig.props(Props(new GetLicense(endProbe.ref))),
  "poolRouter"               // <-- 설정에 정의된 이름
)
```

```scala
akka.actor.deployment {
  /poolRouter {              // 라우터의 전체 이름
    router = balancing-pool  // 라우티가 사용할 로직
    nr-of-instances = 5      // 풀에 있는 라우티의 수
  }
}
```

---

_코드로 풀라우터 생성_

```scala
val router = system.actorOf(
  BalancingPool(5).props(Props(new GetLicense(endProbe.ref))),
  "poolRouter"
)

```

_라우터에게 메시지 보내기_

```scala
router !  Photo("123xyz", 60)
```

---

_원격서버에 라우티를 인스턴스화하는 방법_

```scala
val addresses = Seq(
  Address("akka.tcp", "GetLicenseSystem", "192.1.1.20", 1234),
  AddressFromURIString("akka.tcp://GetLicenseSystem@192.1.1.21:1234"))

val routerRemote1 = system.actorOf(
  RemoteRouterConfig(FromConfig(), addresses)
    .props(Props(new GetLicense(endProbe.ref))),
  "poolRouter-config")

val routerRemote2 = system.actorOf(
  RemoteRouterConfig(RoundRobinPool(5), addresses)
    .props(Props(new GetLicense(endProbe.ref))),
  "poolRouter-code")
```

---
    
##### 그룹 라우터

_라우티의 생성만 담당하는 Creator 액터를 하나 만들고 생성_

```scala
class GetLicenseCreator(nrActors: Int) extends Actor {
  override def preStart() {
    super.preStart()
    (0 until nrActors).map { nr =>
      context.actorOf(Props[GetLicense], "GetLicense" + nr)
    }
  }
}

system.actorOf(Props(new GetLicenseCreator(2)), "Creator")

```

---

_설정으로 그룹라우터 생성_

```scala
akka.actor.deployment {
  /groupRouter {                  // 라우터의 루트 이름
    router = round-robin-group    // 라우터가 사용할 로직
    routees.paths = [             // 사용할 라우티의 액터 경로
      "/user/Creator/GetLicense0",
      "/user/Creator/GetLicense1"]
  }
}

val router = system.actorOf(FromConfig.props(), "groupRouter")

```

---

_코드로 그룹라우터 생성_

```scala
val paths = List(
  "/user/Creator/GetLicense0",
  "/user/Creator/GetLicense1")

val router = system.actorOf(
  RoundRobinGroup(paths).props(), "groupRouter")
```

---

_원격서버의 액터를 라우티로_

```scala
akka.actor.deployment {
  /groupRouter {
    router = round-robin-group
    routees.paths = [
      "akka.tcp://AkkaSystemName@10.0.0.1:2552/user/Creator/GetLicense0",
      "akka.tcp://AkkaSystemName@10.0.0.2:2552/user/Creator/GetLicense0"
    ]
  }
}
```

---

_라우티가 종료되었을때 새 액터 만들기_

```scala
class GetLicenseCreator(nrActors: Int) extends Actor {
  override def preStart() {
    super.preStart()
    (0 until  nrActors).map(nr => {
      val child = context.actorOf(
        Props(new GetLicense(nextStep)), "GetLicense" + nr)
      context.watch(child)
    })
  }

  def receive = {
    case Terminated(child) => {
      val newChild = context.actorOf(
        Props(new GetLicense(nextStep)), child.path.name)
      context.watch(newChild)
    }
  }
}
```

---

##### ConsistentHasing 라우터

- 라우터를 사용하면 규모 확장이 용이하지만
- 메시지가 여러 라우티에 분산됨에 따라
- 순서나 컨텍스트를 고려할 필요가 있을때는
- 특별한 처리가 필요한데 그때 이게 필요

![130%](https://dpzbhybb2pdcj.cloudfront.net/roestenburg/Figures/09fig05_alt.jpg)

---

_메시지로부터 메시지 키를 만드는게 핵심 (3가지 방법)_

- 라우터 내에 정의된 부분 함수 사용
  - 라우터에 따라 서로 다른 결정을 할 수 있음

- 메시지에 해시 매핑을 넣는 방법
  - 사용한 메시지에 따라 서로 다른 결정

- 송신자가 해시 매핑을 아는 경우
  - 송신자에 따라 다른 결정, 사용할 메시지키를 송신자가 알 수 있음 

---

_여러 메시지를 합치는 이런 액터가 있다고 치고.._

```scala
trait GatherMessage {
  val id: String
  val values: Seq[String]
}
case class GatherMessageNormalImpl(id:String, values:Seq[String]) extends GatherMessage
class SimpleGather(nextStep: ActorRef) extends Actor {
  var messages = Map[String, GatherMessage]()
  def receive = {
    case msg: GatherMessage => {
      messages.get(msg.id) match {
        case None => messages += msg.id -> msg
        case Some(previous) =>
          nextStep ! GatherMessageNormalImpl(msg.id, previous.values ++ msg.values)
          messages -= msg.id
      }
    }
  }
}
```

---

`라우터 내에 정의된 부분 함수 사용`
```scala
def hashMapping: ConsistentHashMapping = {
  case msg: GatherMessage => msg.id
}

val router = system.actorOf(
  ConsistentHashingPool(10,
    virtualNodesFactor = 10,     // 라우티당 가상 해시 노드 수
    hashMapping = hashMapping    // 해시 매핑 함수 지정
  ).props(Props(new SimpleGather(endProbe.ref))),
  name = "routerMapping"
)
```

```scala
router ! GatherMessageNormalImpl("1", Seq("msg1"))
router ! GatherMessageNormalImpl("1", Seq("msg2"))
endProbe.expectMsg(GatherMessageNormalImpl("1",Seq("msg1","msg2")))
```

---

`메시지에 해시 매핑을 넣는 방법`

```scala
import akka.routing.ConsistentHashingRouter.ConsistentHashable

case class GatherMessageWithHash(id: String, values: Seq[String])
  extends GatherMessage with ConsistentHashable {

  override def consistentHashKey: Any = id
}
```

```scala
val router = system.actorOf(
  ConsistentHashingPool(10, virtualNodesFactor = 10)
    .props(Props(new SimpleGather(endProbe.ref))),
  name = "routerMessage"
)

router ! GatherMessageWithHash("1", Seq("msg1"))
router ! GatherMessageWithHash("1", Seq("msg2"))
endProbe.expectMsg(GatherMessageNormalImpl("1",Seq("msg1","msg2")))
```

---

`송신자가 해시 매핑을 아는 경우`

```scala
import akka.routing.ConsistentHashingRouter.ConsistentHashableEnvelope

val router = system.actorOf(
  ConsistentHashingPool(10, virtualNodesFactor = 10)
    .props(Props(new SimpleGather(endProbe.ref))),
  name = "routerMessage"
)

router ! ConsistentHashableEnvelope(
  message = GatherMessageNormalImpl("1", Seq("msg1")), hashKey = "1")
router ! ConsistentHashableEnvelope(
  message = GatherMessageNormalImpl("1", Seq("msg2")), hashKey = "1")
endProbe.expectMsg(GatherMessageNormalImpl("1",Seq("msg1","msg2")))
```

---

### Thanks