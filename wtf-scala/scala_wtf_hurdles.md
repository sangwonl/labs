---
marp: true
theme: gaia
---

# WTF Series for understanding Scala
##### 2018. 05. 26
###### Sangwon Lee

---

### 동기

Scala를 쓰면서 허들(hurdle)로 느껴졌던 부분을 정리해둬서 다음에 다시 찾아보거나 새로 배우시는 분들께 참고가 되었으면 함.

---

### 자주 찾는 문서

* History(Origin)
https://www.artima.com/scalazine/articles/origins_of_scala.html

* Tutorial
https://docs.scala-lang.org/tutorials/tour/basics.html.html

* Code Conventions
https://docs.scala-lang.org/style/
https://github.com/databricks/scala-style-guide

* Online Playground
https://scalafiddle.io/

* Monoid, Monads, Functors
https://engineering.sharethrough.com/blog/2016/04/18/explaining-monads-part-1/	

---

# WTF - Code Block with `{}`

보통 여러줄의 코드를 `{}`로 묶어 코드블록이라고 하는건 맞는데, 스칼라에서는 이 블록을 어딘가에 assign 한다거나 함수의 파라미터로 넘기는 등, 좀 더 `first class` 대접을 해준다는 느낌.

---

###### 함수 body 로써의 코드블록

```scala
def sayHello: String = "hello"
def sayHello: String = {
  val greeting = "hello"
  greeting	// <- the last line evaluated is
                // the result of a code block.
}
```

###### 변수로써 코드블록

```scala
val codeBlock = {
  println("tick")
  5
}
println("tack")                            // output:
val evaluated = codeBlock                  // tick
                                           // tack
println("tock")                            // tock
println(evaluated)                         // 5
```

---

###### 함수 parameter로써 코드블록

```scala
def printArea(l: Int, area: Int => Unit): Unit = {
  area(l)
}

printArea(10, { l =>
  println(s"square area: ${l * l}")
})

printArea(10, { l =>
  println(s"triangle area: ${l * l / 2}")
})

printArea(10, { l =>
  import scala.math.Pi
  println(s"circle area: ${l * l * Pi}")
})
```

---

###### `()` vs `{}` 중에 어떤거?

```scala
val l = List(1, 2, 3, 4, 5)

println(l.map(l => l * 2))
// List(2, 4, 6, 8, 10)

println(l.map(_ * 2))
// List(2, 4, 6, 8, 10)

println(l.map { l => println(l); l * 2 })
// List(2, 4, 6, 8, 10)

println(l.map(l => println(l); l * 2))
// error: ')' expected but ';' found.

println(l.map({ l => l * 2 }))
// List(2, 4, 6, 8, 10)
```

---

# WTF - Currying

함수를 first class 로 다루는 언어에서 종종 사용하는 기법 중 하나.

다중 파라미터들을 한번의 함수콜로 그냥 쓸 수도 있지만, 파라미터들을 특성에 맞게 그룹핑을 하고 함수콜도 그에 맞춰 여러 단계로 콜할때 사용할 수 있게 해주는 기능.

---

###### Javascript 로 예를 들자면,

```javascript
function add (a) {
  return function (b) {
    return a + b;
  }
}

add(3)(4);                   // 이렇게 해도 되고

var add3 = add(3);           // 보통은 요렇게..
add3(4);                     // 7
```

---

###### Scala 에서는 문법적으로 지원,

```scala
def add(a: Int)(b: Int): Int = {
  a + b
}

val add3: Int => Int = add(3)

println(add3(4))             // 7

```

---

# WTF - `Nothing` vs `Null`

타입하면 이 그림. 타입은 크게 `Any`를 기반으로 value(primitive) 타입인 `AnyVal`과 reference 타입인 `AnyRef`로 나뉘고, `AnyRef`같은 경우는 `Null` 을 subtype 으로 가지며 이를 포함한 모든 타입의 subtype 으로는 `Nothing` 이 있음. 그런데...

![100%](https://i.stack.imgur.com/i19XD.png)

---

###### Null 은 어디서 쓴다는 말인가?


```scala
null.isInstanceOf[List[Int]]              // true
null.isInstanceOf[Seq[String]]            // true
null.isInstanceOf[Any]                    // true
null.isInstanceOf[AnyRef]                 // true
null.isInstanceOf[AnyVal]                 // error

val nullList: List[Int] = null            // ok
val nullMap: Map[String, String] = null   // ok
val someInt: Int = null                   // error
```

---

###### Nothing 은 어디서 쓴다는 말인가?

```scala
// There's the only case of using Nothing type
// as return type of a function that must not return
// due to throwing exception of termination signal..

def mustNotReturnBut: Nothing = {
  10
}
// error: type mismatch;
// found   : scala.this.Int(10)
// required: scala.this.Nothing

def mustNotReturnSo: Nothing = {
  throw new Exception("it can not react at the end")
}
// ok
```

---

# WTF - Call by value vs name


```scala
// call-by-value
// 함수가 수행되기 전에 파라미터가 먼저 평가됨.
def first(a: Int, b: Int): Int = a
first(3 + 4, 5 + 6)
// 1. first(7, 5 + 6)
// 2. first(7, 11)
// 3. 7

// call-by-name
// 파라미터 평가되지 않은 상태로 함수에 그대로 전해진 후
// 함수가 평가될때 대체됨.
def first1(a: => Int, b: Int): Int = a
first1(3 + 4, 5 + 6)
// 1. (3 + 4)
// 2. 7
```

---

```scala
def something(): Unit = {
  println("calling something")
  1   // return value
}

def callByValue(x: Int): Unit = {
  println("x1=" + x);  println("x2=" + x)
}

def callByName(x: => Int): Unit = {
  println("x1=" + x); println("x2=" + x)
}

scala> callByValue(something())
calling something
x1=1
x2=1

scala> callByName(something())
calling something
x1=1
calling something
x2=1
```

---

# WTF - Where is class `constructor`

Scala 에서 처음 `class` 를 접했을때 생성자가 어디갔지? instantiation 할때 어떤 인자를 넘기지? 라고 당황했었음. 그러나 결국 그 우아함에 굴복, 그 편리함의 노예가 됨.

아래 예제가 scala 가 추구하는 철학을 보여준다고 생각함. 저 코드에서 무엇을 더 뺄 수 있을까. 더이상 뺄 것이 없는 완벽히 간결한 **Simplicity!**

```scala
class User

val 군더더기가_있다면_그것은_나의_몫 = new User     // 이거 됨.
```

---

###### 일단 기본 생성자 (및 멤버변수)

```scala
class Point(var x: Int, var y: Int) {
  val z = 4        // x, y, z 모두 멤버 변수
  override def toString: String = s"($x, $y, $z)"
}

val pt = new Point(2, 3)
println(pt.x)     // 2
println(pt.z)     // 4

pt.x = 20         // ok
pt.y = 30         // ok
pt.z = 40         // error (not allow to set for `val`)

println(pt)       // (20, 30, 4)
```

---

###### 멤버 변수 접근 제어

```scala
class Point(x: Int, val y: Int) {
  private var z = 4   // body에 정의한 멤버는 private 접근자로
  override def toString: String = s"($x, $y, $z)"
}

val pt = new Point(2, 3)
println(pt.x)     // error (x is private by default)
println(pt.z)     // error (z is explictly private)
pt.z = 40         // error (z is `var` but not visible)

println(pt.y)     // 3 (ok to access `val`)
pt.y = 30         // error (can't set for `val`)

println(pt)       // (2, 3, 4)
```

---

###### 생성자 오버라이딩

```scala
class Foo(x: Int, y: Int, z: String) {  
  // default y parameter to 0  
  def this(x: Int, z: String) = this(x, 0, z)   
  
  // default x & y parameters to 0
  // calls previous auxiliary constructor
  // which calls the primary constructor  
  def this(z: String) = this(0, z);   
}
```

---

# WTF - `case class`

`class` 가 있는데 이건 왜 또? `class` 가 클래스라는 역할을 충실히 하고 있다면, 이것은 immutable 한 데이터의 모델링에 최적화하기 위해 `class` 에 약간의 양념을 쳤달까? 다음과 같은 MSG..

- case class (constructor)의 paremter가 기본으로 public & val
- parameter 가 val 라서 reassign  못함 (immutable)
- 내부적으로 `apply` 메소드가 있어서 이녀석이 object 생성을 담당하기 때문에 `new` 키워드를 안써도 됨
- 컴파일러가 comparison 을 지원함 
- copy도 지원함
- pattern matching 의 case 에 타입 식별로 쓸 수 있음 (그래서 `case`?)

---

###### 정의

```scala
case class Message(
  sender: String,         // public val
  recipient: String,      // by default
  body: String
)

val msg = Message(        // no need `new` keyword
  "abc@def.com",
  "xyz@vuw.com",
  "Hi, there?"
)

println(msg.sender)
// abc@def.com
```

---

###### Comparison & Copy

```scala
case class Message(recipient: String, body: String)

val msg1 = Message("abc@def.com", "Hi, there?")
val msg2 = Message("abc@def.com", "Hi, there!")

println(msg1 == msg2)
// false

val msg3 = msg2.copy(body = "Hi, there?")
println(msg1 == msg3)
// true
```

---

###### Pattern Matching

```scala
trait Animal
case class Dog(name: String, age: Int) extends Animal
case class Cat(name: String) extends Animal
case object Woodpecker extends Animal

def determineType(x: Animal): String = x match {
  case Dog(moniker, age) =>
    s"Got a Dog, name = $moniker and age = $age"
  case _: Cat => "Got a Cat (ignoring the name)"
  case Woodpecker => "That was a Woodpecker"
  case _ => "That was something else"
}
  
println(determineType(new Dog("Rocky", 10)))
println(determineType(new Cat("Rusty the Cat")))
println(determineType(Woodpecker))
```

---


# WTF - `trait` vs `abstract class`

여기저기 찾아보면 `trait` 은 java의 `interface` 와 비슷한거라고 많이 비교하는데 method body 를 구현할 수 있는거 보면 완전히 같은 개념은 아닌 것 같고 또 `abstract class` 도 별도로 있는데 어떻게 구분하면 좋을까?

---

| features                 | `trait`                 | `abstract class`                       |
| ------------------------ |:-----------------------:| --------------------------------------:|
| parameter                | type parameter only     | constructor parameter + type parameter |
| interoperate with Java   | Yes with pure methods   | Always Yes                             | 
| inheritance              | multiple                | only one                               |
| as mixins                | Yes with implementation | No                                     |

---

# WTF - Companion Object

scala 에서 `object` 는 보통 `lazy val` 되는 singleton class instance 로 많이 쓰는데 특정 `class` 와 동일한 이름의 `object` 를 정의하면 해당 클래스와 짝궁(pair)이 되는데 이를 `companion object` 라고 함. 이를 이용하면 해당 클래스의 factory 처럼 쓸 수 있음.

---

###### Like a class factory

```scala
class Email(val username: String, val domain: String)

object Email {
  def fromString(email: String): Email = {
    val s = email.split("@")
    new Email(s.head, s.last)
  }
  
  def apply(email: String): Email = fromString(email)
}

val e1 = Email.fromString("abc@xyz.com")
println(e1.username)
println(e1.domain)

val e2 = Email("abc@xyz.com")
println(e2.username)
println(e2.domain)
```

---

# WTF - Pattern Matching

이게 또.. scala 의 진미 중 하나. `switch-case` 의 진화의 끝이랄까. 이 패턴매칭의 매칭은 크게 네가지 종류가 있음.

- 값으로 Matching
- `case class` 로 Matching
- Pattern Guard (simple boolean expression) 로 Matching
- Type 으로 Matching

---

###### Matching by value

```scala
import scala.util.Random

val numName: String = Random.nextInt(10) match {
  case 0 => "zero"
  case 1 => "one"
  case 2 => "two"
  case _ => "many"
}

println(numName)
// many (for my case..)
```

---

###### Matching by `case class`

```scala
abstract class Noti
case class Msg(title: String, body: String) extends Noti
case class SMS(caller: String, body: String) extends Noti
case class VoiceRecording(link: String) extends Noti

def showNoti(noti: Noti): String = {
  noti match {
    case Msg(title, _) =>
      s"You got an message with title: $title"
    case SMS(number, message) =>
      s"You got an SMS from $number! Message: $message"
    case VoiceRecording(link) =>
      s"Got a voice, click the link to hear it: $link"
  }
}

println(showNoti(Msg("제목", "바디")))
// You got an message with title: 제목
println(showNoti(SMS("번호", "바디")))
// You got an SMS from 번호! Message: 바디
println(showNoti(VoiceRecording("링크")))
// Got a voice, click the link to hear it: 링크
```

---

###### Matching by pattern guard

```scala
import scala.util.Random

Random.nextInt(10) match {
  case a if 0 to 9 contains a =>
    println("0-9 range: " + a)
  case b if 10 to 19 contains b =>
    println("10-19 range: " + b)
  case c if 20 to 29 contains c =>
    println("20-29 range: " + c)
  case _ =>
    println("Hmmm...")
}
// 0-9 range: 3 (for my case)
```

---

###### Matching by type

```scala
abstract class Device
case class Phone(model: String) extends Device {
  def screenOff = "Turning screen off"
}

case class Computer(model: String) extends Device {
  def screenSaverOn = "Turning screen saver on..."
}

def goIdle(device: Device) = device match {
  case p: Phone => p.screenOff
  case c: Computer => c.screenSaverOn
}

println(goIdle(Phone("iphone6s")))
// Turning screen off

println(goIdle(Computer("macbook")))
// Turning screen saver on...
```

---

# WTF `FuctionN`, `TupleN`

scala 에서 종종 쓰게 되는 구문 중에 익명 함수 혹은 튜플이 있는데, 이들은 scala 내부에서 어떻게 지원되고 있는걸까?

- Anonymous Function
  ```scala
  val quickSum = (a: Int, b: Int) => a + b
  println(quickSum(1, 2))      // 3
  ```
- Tuple
  ```scala
  val tuple = (1, 2, 3)
  println(tuple)               // (1, 2, 3)
  ```

---

###### Function Type

```scala
val quickSum = (a: Int, b: Int) => a + b

// 익명 함수를 아래처럼 FunctionN 을 이용해 명시적으로 정의할 수 있음.
// Function0 ~ Function22 까지 미리 정의되어 있고,
// type parameter 에서 마지막이 return type 나머지는 함수 인자.
val quickSum2 = new Function2[Int, Int, Int] {
  def apply(a: Int, b: Int): Int = a + b
}

assert(quickSum(1, 2) == quickSum2(1, 2))   // ok
```

---

###### Tuple Type (Tuple1 ~ Tuple22)

```scala
val tuple = (1, 2, 3)
println(tuple)
// (1, 2, 3)

val tuple2 = Tuple3[Int, Int, Int](1, 2, 3)
println(tuple2._1, tuple2._3)
// (1, 3)

val tuple3 = Tuple3(1, 2, 3)
println(tuple3)
// (1, 2, 3)

val tuple4 = Tuple4(1, 2, 3)                    // error
println(tuple4)

val tuple5 = Tuple3[Int, Int, Int](1, "two", 3) // error
println(tuple3)
```

---

# WTF - `Option`, `Either` and `Try`

처음에는 어색했지만 정말 훌륭한 아이디어라는 생각이드는 feature. 변수라는건 보통 특정 값을 가지고 있기는 하지만 종종 `어떤 값도 정해지지 않는 상태` 를 표현하고 싶을때도 있다. 그래서 reference type 의 경우에는 그런 상태를 `null` 이라는 값으로 이용하기도 하죠. 그러나 primitive type, 가령 integer 일 경우에는 `0` 으로 그 상태를 표현할 수 있을까?

scala 에서는 실제 값 외에 이런 상태들을 함께 표현할 수 있는 wrapper 클래스를 builtin 으로 제공합니다.

- `Option[T]` - 특정 값이 있거나 없는 상태 `Some(T타입값)` or `None`
- `Either[L, R]` - `Left(L타입값)` or `Right(R타입값)`
- `Try[T]` - `Success(T타입값)` or `Failure(T타입값)`

---

###### Option Usage

```scala
def toInt(s: String): Option[Int] = {
    try {
        Some(Integer.parseInt(s.trim))
    } catch {
        case e: Exception => None
    }
}

val x1 = toInt("1")                 // Some(1)
x1.isEmpty                          // false
val x2 = toInt("1").getOrElse(0)    // 1
val x3 = toInt("foo")               // None
val x4 = toInt("foo").getOrElse(0)  // 0

toInt("10").foreach{ i => println(s"Got an int: $i") }
// Got an int: 10

toInt("10") match {
  case Some(i) => println(i)
  case None => println("That didn't work.")
}
// 10
```

---

###### Either Usage

```scala
def divideXByY(x: Int, y: Int): Either[String, Int] = {
  if (y == 0) Left("Dude, can't divide by 0")
  else Right(x / y)
}

val x1 = divideXByY(1, 1).right.getOrElse(0)  // 1
val x2 = divideXByY(1, 1).left.get            // error
val x3 = divideXByY(1, 0).right.getOrElse(0)  // 0
val x4 = divideXByY(1, 0).left.get
println(x4)
// Dude, can't divide by 0

divideXByY(1, 0) match {
    case Left(s) => println("Answer: " + s)
    case Right(i) => println("Answer: " + i)
}
// Answer: Dude, can't divide by 0
```


---

###### Try Usage

```scala
// Introduced from scala 2.10
// Try[T] is convenient version of Either[Throwable, T]

import scala.util.Try

def toInt(s: String): Try[Int] = {
    Try(Integer.parseInt(s.trim))
}

val x = toInt("1")        // Success(1)
x.isSuccess               // true
x.isFailure               // false
toInt("1").getOrElse(0)   // 1
toInt("one")              // Failure(java.lang.NumberFormatException: For input string: "one")
toInt("one").getOrElse(0) // 0

toInt("1") match {
  case Success(i) => println(i)  // 1
  case Failure(e) => println(e)
}
```

---

# WTF - Implicit Parameters

종종 순차적으로 혹은 중첩되어 호출되는 함수에 계속 따라다니는 파라미터를 넘기게되는 경우가 있다. 이런 군더더기 같은 파라미터들을 scala 에서는 `implicit` 로 풀었다. 하지만 가독성을 위해 너무 남발하면 No No.

```scala
def nestedProc()(implicit sw: StopWatch): Unit = {
  ...
}

def proc(key: String)(implicit sw: StopWatch): Unit = {
  sw.tap
  ...  
  nestedProcess()
  ...
}

implicit val sw = new StopWatch

proc("job-id-123")
// 이 스코프에서 해당 타입의 implicit 변수를 lookup, 없으면 error.
```

---

# WTF - Implicit Conversions

이 부분도 scala 의 꽃 중의 하나다. 강타입 언어임에도 불구하고 얼마나 간결한 언어를 만들고 싶어하는지의 철학을 엿볼 수 있는 부분. 어떤 타입에서 다른 타입의 값으로 변환할때 종종 이런 코드를 쓴다.

```scala
case class Person(name: String, tall: Int)
case class Fly(name: String, tall: Int)

object Fly {
  def fromPerson(p: Person): Fly = {
    Fly(s"fly-${p.name}", p.tall / 10)
  }
}

val p = Person("eddy", 190)
val f = Fly.fromPerson(p)
println(f)         // Fly(fly-eddy,19)
```

---

###### 하지만 이건 어떠한가?

```scala
case class Person(name: String, tall: Int)
case class Fly(name: String, tall: Int)

implicit def personToFly(p: Person): Fly = {
  Fly(s"fly-${p.name}", p.tall / 10)
}

val p = Person("eddy", 190)
val f: Fly = p     // 이보다 더 간결할 수 있는가!
                   // Person -> Fly 로 변환하는 implict
                   // 함수가 있는지 lookup, 없으면 error.

assert(f.name == "fly-eddy")
assert(f.tall == 19)
```

---

# WTF - Future

...

---
