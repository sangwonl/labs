---
marp: true
theme: gaia
---

# ![](https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/Akka_toolkit_logo.svg/1200px-Akka_toolkit_logo.svg.png)
#### 2018. 03. 31
###### Sangwon Lee

---

### Background

Many common practices and accepted programming models do not address important challenges inherent in designing systems for modern computer architectures. To be successful, **_distributed systems must cope in an environment where components crash without responding, messages get lost without a trace on the wire, and network latency fluctuates. These problems occur regularly in carefully managed intra-datacenter environments - even more so in virtualized architectures._**

---

### Challenges
##### The challenge of encapsulation

---

#### The challenge of encapsulation

- We have 3-objects, it depnds on each other.

![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/seq_chart.png)

---

- In single thread environment, no problem.

![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/seq_chart_thread.png)

---

- Under multi-threaded environment,

![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/seq_chart_multi_thread.png)


![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/object_graph_snakes.png)

---

In summary,

- Objects can only guarantee encapsulation in the face of single-threaded access, multi-thread execution almost always leads to corrupted internal state.

- While locks seem to be the natural remedy to uphold encapsulation with multiple threads, in practice they are inefficient and easily lead to deadlocks in any application of real-world scale.

- Locks work locally, attempts to make them distributed exist, but offer limited potential for scaling out.

---

#### The illusion of shared memory on modern computer architectures

- Programming models of the 80’-90’s conceptualize that writing to a variable means writing to a memory location directly.

- On modern architectures, CPUs are writing to cache lines instead of writing to memory directly.

---

##### So,
- There is no real shared memory anymore, CPU cores pass chunks of data (cache lines) explicitly to each other just as computers on a network do. 

- Inter-CPU communication and network communication have more in common than many realize. Passing messages is the norm now be it across CPUs or networked computers.

- To keep state local to a concurrent entity and propagate data or events between concurrent entities explicitly via messages.

---

#### The illusion of a call stack

![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/exception_prop.png)

---

- how can the “caller” be notified of the completion of the task?

- When a task fails with an exception, where does the exception propagate to?

- This bad situation gets worse when things go really wrong and a worker backed by a thread encounters a bug and ends up in an unrecoverable situation.

---

##### So,

- To achieve any meaningful concurrency and performance on current systems, threads must delegate tasks among each other in an efficient way **without blocking**.

- With this style of task-delegating concurrency call stack-based error handling breaks down and new, **explicit error signaling mechanisms** need to be introduced. Failures become part of the domain model.

- **Concurrent systems** with work delegation needs to handle service **faults** and have principled means to **recover** from them.

---

### Finally, we got AKKA

###### AKKA provides

- Multi-threaded behavior without the use of low-level concurrency constructs like atomics or locks.

- Transparent remote communication between systems and their components.

- A clustered, high-availability architecture that is elastic, scales in or out, on demand.

---

### The name AKKA comes from

- It is the name of a beautiful Swedish mountain up in the northern part of Sweden called Laponia.

- Akka is also the name of a goddess in the Sámi (the native Swedish population) mythology. She is the goddess that stands for all the beauty and good in the world.

- Also, the name AKKA is a palindrome of the letters A and K as in `Actor Kernel`.

---

### Actor Model

---

### Concept
##### How does it work?

![](https://ljcbookclub.files.wordpress.com/2012/02/actors.png)

---

### Benefit

- Enforce encapsulation without resorting to locks.

- Use the model of cooperative entities reacting to signals, changing state, and sending signals to each other to drive the whole application forward.

- Stop worrying about an executing mechanism which is a mismatch to our world view.

---

![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/actor_graph.png)

    An important difference between passing messages and
    calling methods is that messages have no return value.
    By sending a message, an actor delegates work to another
    actor. As we saw in The illusion of a call stack, if it
    expected a return value, the sending actor would either
    need to block or to execute the other actor’s work on the
    same thread. Instead, the receiving actor delivers
    the results in a reply message.

---

![](https://doc.akka.io/docs/akka/2.5/guide/diagrams/serialized_timeline_invariants.png)

	1. The actor adds the message to the end of a queue.
    2. If the actor was not scheduled for execution,
       it is marked as ready to execute.
    4. A (hidden) scheduler entity takes the actor
       and starts executing it.
    6. Actor picks the message from the front of the queue.
    7. Actor modifies internal state,
       sends messages to other actors.
    9. The actor is unscheduled.

---

### Consist of

### `A mailbox`
the queue where messages end up

### `A behavior`
the state of the actor, internal variables etc.

### `Messages`
pieces of data representing a signal, similar to method calls and their parameters.

--- 

### `An execution environment`
the machinery that takes actors that have messages to react to and invokes their message handling code.

### `An address`
url that refers to the actor instnace. as contact point of an actor receiving messages.

---

# Example

https://developer.lightbend.com/guides/akka-quickstart-scala/?_ga=2.181057071.943154346.1522457793-973825023.1521697278?_ga=2.181057071.943154346.1522457793-973825023.1521697278

https://doc.akka.io/docs/akka/2.5/guide/tutorial.html
