import Commander

let main = command { (filename: String) in
  print("Reading file \(filename)...")
}

main.run()
