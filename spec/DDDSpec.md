# Domain-Driven Design (DDD) Core Principles

This project strictly adheres to Domain-Driven Design. All code contributions must align with the following three core principles.

## 1. Ubiquitous Language (通用语言)
**Goal:** Eliminate the gap between domain experts and technical implementation. Code is documentation.

*   **English Instruction:**
    > **Principle: Strict Adherence to Ubiquitous Language**
    > Naming in the codebase (classes, methods, variables, modules) must rigorously align with the consensus terminology used by domain experts. **Do not perform technical "translations" or abstractions.** If the business calls it a "Booking," the code must not call it a "Reservation" or "Order." Ubiquitous Language is not just about nouns; it dictates **domain behaviors**. Method names must express business intent (e.g., `issue_refund()`) rather than CRUD operations (e.g., `set_refund_status()`). When domain concepts evolve, the code must be refactored to reflect the new linguistic model.

*   **中文原则:**
    > **严禁进行技术性的“翻译”或抽象**。代码中的命名必须严格通过与领域专家的共识术语保持一致。方法名应描述业务意图（如 `issue_refund()`），而非单纯的数据操作（如 `set_refund_status()`）。代码是领域知识的直接投影，阅读代码应能直接理解业务逻辑。

## 2. Bounded Context (限界上下文)
**Goal:** Define explicit model boundaries to prevent conceptual confusion.

*   **English Instruction:**
    > **Principle: Model Isolation via Bounded Contexts**
    > Distinctly define the semantic boundaries of models. The same term represents completely different concepts in different contexts (e.g., a "Product" in Sales vs. Logistics). **Strictly forbid the creation of "God Objects".**
    > 1.  **Explicit Boundaries:** Each context must have clear physical code boundaries (modules/packages/services).
    > 2.  **Context Mapping:** Cross-context interactions must utilize Anti-Corruption Layers (ACL) or Open Host Services (OHS). Never directly reference another context's database or internal objects.
    > 3.  **Unambiguity:** Within a single context, the Ubiquitous Language must be unambiguous.

*   **中文原则:**
    > **通过限界上下文隔离模型**。同一个术语在不同上下文中代表不同概念，严禁创建试图涵盖所有场景的“上帝对象”。跨上下文交互必须通过防腐层（ACL）或开放主机服务（OHS），严禁直接引用其他上下文的数据库或内部对象。

## 3. Aggregates & Rich Domain Model (聚合与充血模型)
**Goal:** Enforce data consistency (Invariants) and encapsulate logic.

*   **English Instruction:**
    > **Principle: Rich Domain Model with Aggregates**
    > Reject the "Anemic Domain Model" (classes with only data and Getters/Setters). Entities and Value Objects must encapsulate business logic and validation.
    > 1.  **Aggregate Root as Gateway:** The Aggregate is the atomic unit of data modification. External objects can only hold references to the Aggregate Root; direct access to internal entities is prohibited.
    > 2.  **Enforce Invariants:** The Aggregate Root must ensure all business rules remain satisfied after any state change.
    > 3.  **Transactional Boundaries:** A single transaction should modify only one Aggregate instance. Use Domain Events for eventual consistency.

*   **中文原则:**
    > **拒绝贫血模型**。实体和值对象必须包含业务逻辑验证。聚合根是数据修改的最小原子单元，外部对象严禁直接访问聚合内部实体。聚合根必须确保在任何状态变更后，整体业务规则（不变量）依然成立。

## 4. 项目聚合风格

按业务一致性边界划分聚合
