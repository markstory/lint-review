defmodule HasErrors do
  def f(x) do
    Enum.map(x, fn y -> y end) |> Enum.map(fn z -> z end)
  end
end
