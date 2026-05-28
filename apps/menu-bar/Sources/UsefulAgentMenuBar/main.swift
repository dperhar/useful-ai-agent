import AppKit
import Foundation

final class UsefulAgentApp: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)

    func applicationDidFinishLaunching(_ notification: Notification) {
        item.button?.image = Self.agentIcon()
        item.button?.toolTip = "Useful AI Agent"
        let menu = NSMenu()
        menu.delegate = self
        item.menu = menu
    }

    func menuWillOpen(_ menu: NSMenu) {
        rebuildMenu(menu)
    }

    private func rebuildMenu(_ menu: NSMenu) {
        menu.removeAllItems()
        menu.addItem(item("Doctor / Health", #selector(check)))
        menu.addItem(item("Start", #selector(start)))
        menu.addItem(item("Stop", #selector(stop)))
        menu.addItem(item("Restart", #selector(restart)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Backup Now", #selector(backup)))
        menu.addItem(mirrorStatusItem())
        menu.addItem(item("Choose Backup Mirror Folder...", #selector(chooseMirrorFolder)))
        menu.addItem(item("Disable Backup Mirror", #selector(disableMirror)))
        menu.addItem(restoreLatestMenu())
        menu.addItem(item("Restore From File...", #selector(restoreFromFile)))
        menu.addItem(item("Open Backup Folder", #selector(openBackupFolder)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Show Local Health", #selector(openConsole)))
        menu.addItem(item("Open Telegram Setup", #selector(openTelegram)))
        menu.addItem(item("View Logs", #selector(logs)))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(item("Quit", #selector(quit)))
    }

    private func item(_ title: String, _ action: Selector) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: "")
        item.target = self
        return item
    }

    private func mirrorStatusItem() -> NSMenuItem {
        let status = runCapture(["backup", "mirror", "status"])
        var title = "Backup Mirror: Unknown"
        if let data = status.data(using: .utf8),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            let enabled = (json["enabled"] as? Bool) ?? false
            let path = (json["path"] as? String) ?? ""
            title = enabled ? "Backup Mirror: Enabled" : "Backup Mirror: Disabled"
            if enabled && !path.isEmpty {
                title += " -> " + NSString(string: path).lastPathComponent
            }
        }
        let menuItem = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        menuItem.isEnabled = false
        return menuItem
    }

    private func restoreLatestMenu() -> NSMenuItem {
        let parent = NSMenuItem(title: "Restore From Latest", action: nil, keyEquivalent: "")
        let submenu = NSMenu()
        let output = runCapture(["backup", "list", "--json", "--limit", "5"])
        if let data = output.data(using: .utf8),
           let backups = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
           !backups.isEmpty {
            for (offset, backup) in backups.enumerated() {
                let created = (backup["created_at"] as? String) ?? "unknown date"
                let artifact = (backup["artifact"] as? String) ?? ""
                let title = "\(offset + 1). \(created) \(NSString(string: artifact).lastPathComponent)"
                let child = item(title, #selector(restoreLatest(_:)))
                child.representedObject = offset + 1
                submenu.addItem(child)
            }
        } else {
            let empty = NSMenuItem(title: "No backups found", action: nil, keyEquivalent: "")
            empty.isEnabled = false
            submenu.addItem(empty)
        }
        parent.submenu = submenu
        return parent
    }

    @objc private func check() { runAndAlert(["doctor"]) }
    @objc private func start() { runAndAlert(["start"]) }
    @objc private func stop() { runAndAlert(["stop"]) }
    @objc private func restart() { runAndAlert(["restart"]) }
    @objc private func backup() { runAndAlert(["backup"]) }
    @objc private func logs() { runAndAlert(["logs"]) }
    @objc private func openConsole() { runAndAlert(["doctor"]) }
    @objc private func openTelegram() { runAndAlert(["open-telegram-setup"]) }
    @objc private func openBackupFolder() { runAndAlert(["backup", "open-folder"]) }
    @objc private func disableMirror() { runAndAlert(["backup", "mirror", "disable"]) }
    @objc private func quit() { NSApplication.shared.terminate(nil) }

    @objc private func chooseMirrorFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Use This Folder"
        if panel.runModal() == .OK, let url = panel.url {
            runAndAlert(["backup", "mirror", "enable", "--path", url.path])
        }
    }

    @objc private func restoreFromFile() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.allowedFileTypes = ["enc"]
        panel.prompt = "Restore Backup"
        if panel.runModal() == .OK, let url = panel.url {
            runAndAlert(["backup", "restore", "--file", url.path])
        }
    }

    @objc private func restoreLatest(_ sender: NSMenuItem) {
        guard let index = sender.representedObject as? Int else { return }
        runAndAlert(["backup", "restore", "--latest", "\(index)"])
    }

    private func runAndAlert(_ args: [String]) {
        let output = runCapture(args)
        let alert = NSAlert()
        alert.messageText = "Useful AI Agent"
        alert.informativeText = output.isEmpty ? "Command finished." : String(output.suffix(2000))
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }

    private func runCapture(_ args: [String]) -> String {
        let process = Process()
        let pipe = Pipe()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", "useful-agent " + args.map(Self.shellQuote).joined(separator: " ")]
        process.standardOutput = pipe
        process.standardError = pipe
        do {
            try process.run()
            process.waitUntilExit()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            return String(data: data, encoding: .utf8) ?? ""
        } catch {
            return "Failed to run useful-agent: \(error.localizedDescription)"
        }
    }

    private static func shellQuote(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: "'\\''") + "'"
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

        NSBezierPath(roundedRect: NSRect(x: 1.7, y: 7.8, width: 2.0, height: 3.2), xRadius: 1.0, yRadius: 1.0).fill()
        NSBezierPath(roundedRect: NSRect(x: 14.3, y: 7.8, width: 2.0, height: 3.2), xRadius: 1.0, yRadius: 1.0).fill()

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
