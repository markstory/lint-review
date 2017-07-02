Group {
  $0.command("login") { (name:String) in
    print("Hello \(name)")
  }

  $0.command("logout") {
    print("Goodbye.")
  }
}
