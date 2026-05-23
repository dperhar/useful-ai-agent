import AppKit
import Foundation

final class UsefulAgentApp: NSObject, NSApplicationDelegate {
    private let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)

    func applicationDidFinishLaunching(_ notification: Notification) {
        item.button?.image = Self.agentIcon()
        item.button?.toolTip = "Useful AI Agent"
        rebuildMenu()
    }

    private func rebuildMenu() {
        let menu = NSMenu()
        menu.addItem(item("Check Health", #selector(check)))
        menu.addItem(item("Start", #selector(start)))
        menu.addItem(item("Stop", #selector(stop)))
        menu.addItem(item("Restart", #selector(restart)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Backup Now", #selector(backup)))
        menu.addItem(item("Show Local Health", #selector(openConsole)))
        menu.addItem(item("Open Telegram Setup", #selector(openTelegram)))
        menu.addItem(item("View Logs", #selector(logs)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Quit", #selector(quit)))
        item.menu = menu
    }

    private func item(_ title: String, _ action: Selector) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: "")
        item.target = self
        return item
    }

    @objc private func check() { run(["check"]) }
    @objc private func start() { run(["start"]) }
    @objc private func stop() { run(["stop"]) }
    @objc private func restart() { run(["restart"]) }
    @objc private func backup() { run(["backup"]) }
    @objc private func logs() { run(["logs"]) }
    @objc private func openConsole() { run(["doctor"]) }
    @objc private func openTelegram() { run(["open-telegram-setup"]) }
    @objc private func quit() { NSApplication.shared.terminate(nil) }

    private func run(_ args: [String]) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", "useful-agent " + args.joined(separator: " ")]
        try? process.run()
    }

    private static func agentIcon() -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        image.lockFocus()

        NSColor.black.setStroke()
        NSColor.black.setFill()

        let stroke = NSBezierPath()
        stroke.lineWidth = 1.7
        stroke.lineCapStyle = .round
        stroke.move(to: NSPoint(x: 9, y: 15.2))
        stroke.line(to: NSPoint(x: 9, y: 16.8))
        stroke.stroke()

        NSBezierPath(ovalIn: NSRect(x: 7.9, y: 16.0, width: 2.2, height: 2.2)).fill()

        let head = NSBezierPath(roundedRect: NSRect(x: 3.2, y: 4.0, width: 11.6, height: 10.6), xRadius: 3.0, yRadius: 3.0)
        head.lineWidth = 1.7
        head.stroke()

        NSBezierPath(ovalIn: NSRect(x: 6.0, y: 9.4, width: 1.9, height: 1.9)).fill()
        NSBezierPath(ovalIn: NSRect(x: 10.1, y: 9.4, width: 1.9, height: 1.9)).fill()

        let mouth = NSBezierPath()
        mouth.lineWidth = 1.5
        mouth.lineCapStyle = .round
        mouth.move(to: NSPoint(x: 6.7, y: 7.1))
        mouth.line(to: NSPoint(x: 11.3, y: 7.1))
        mouth.stroke()

        let leftEar = NSBezierPath(roundedRect: NSRect(x: 1.7, y: 7.8, width: 2.0, height: 3.2), xRadius: 1.0, yRadius: 1.0)
        leftEar.fill()
        let rightEar = NSBezierPath(roundedRect: NSRect(x: 14.3, y: 7.8, width: 2.0, height: 3.2), xRadius: 1.0, yRadius: 1.0)
        rightEar.fill()

        image.unlockFocus()
        image.isTemplate = true
        image.size = size
        return image
    }
}

let app = NSApplication.shared
let delegate = UsefulAgentApp()
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
