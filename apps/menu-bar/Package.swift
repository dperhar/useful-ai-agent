// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "UsefulAgentMenuBar",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "UsefulAgentMenuBar", targets: ["UsefulAgentMenuBar"])
    ],
    targets: [
        .executableTarget(name: "UsefulAgentMenuBar")
    ]
)
