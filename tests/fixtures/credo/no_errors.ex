defmodule NoErrors do
  @moduledoc "This is a module."

  def f do
    g 4
  end

  defp g(x) do
    g * 2
  end
end
