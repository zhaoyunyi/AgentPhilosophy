# Mocking 参考

Mock 只用于真实 seam 上不可控、昂贵或危险的外部能力，例如网络、时钟、随机数或支付网关。

- 优先使用小型 fake adapter，通过与生产相同的 Interface。
- 不 mock 私有函数、内部调用顺序或实现细节。
- 如果测试需要大量 mock 才能到达行为，重新检查模块 Interface 与 seam。
- 契约重要时，让 fake 与真实 adapter 通过同一 contract test。
