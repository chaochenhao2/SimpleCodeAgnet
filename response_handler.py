import json

# ================== 流式响应处理器 ==================
def process_stream(stream):
    '''处理流式响应，提取内容文本和工具调用'''
    content = ""
    tool_calls_dict = {}

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        if delta.content:
            print(delta.content, end="", flush=True)
            content += delta.content

        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_dict:
                    tool_calls_dict[idx] = {"id": None, "name": None, "arguments": ""}
                if tc.id:
                    tool_calls_dict[idx]["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        tool_calls_dict[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_dict[idx]["arguments"] += tc.function.arguments

    if content:
        print()

    tool_calls = []
    for idx in sorted(tool_calls_dict.keys()):
        item = tool_calls_dict[idx]
        if item["id"] and item["name"]:
            tool_calls.append({
                "id": item["id"],
                "type": "function",
                "function": {
                    "name": item["name"],
                    "arguments": item["arguments"]
                }
            })
    return content, tool_calls
