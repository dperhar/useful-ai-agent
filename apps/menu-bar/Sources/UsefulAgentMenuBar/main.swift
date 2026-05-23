import AppKit
import Foundation

final class UsefulAgentApp: NSObject, NSApplicationDelegate {
    private let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

    func applicationDidFinishLaunching(_ notification: Notification) {
        item.button?.title = "UA"
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
        menu.addItem(item("Open Local Console", #selector(openConsole)))
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
    @objc private func openConsole() { run(["open-console"]) }
    @objc private func openTelegram() { run(["open-telegram-setup"]) }
    @objc private func quit() { NSApplication.shared.terminate(nil) }

    private func run(_ args: [String]) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", "useful-agent " + args.joined(separator: " ")]
        try? process.run()
    }
}

let app = NSApplication.shared
let delegate = UsefulAgentApp()
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
