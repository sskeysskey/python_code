def show_results_with_json(results, json_path, keywords):
    matched_names_stocks, matched_names_etfs = search_json_for_keywords(json_path, keywords)
    matched_names_txt = search_txt_for_keywords(txt_path, keywords)

    result_window = Toplevel(root)
    result_window.title("搜索结果")
    window_center(result_window, 800, 600)
    scrollbar = Scrollbar(result_window)
    scrollbar.pack(side="right", fill="y")
    text = Text(result_window, width=120, height=25, yscrollcommand=scrollbar.set)
    text.pack(side="left", fill="both")
    text.tag_configure('directory_tag', foreground='yellow', font=('Helvetica', '24', 'bold'))
    text.tag_configure('file_tag', foreground='orange', underline=True, font=('Helvetica', '20'))
    text.tag_configure('stock_tag', foreground='white', underline=True, font=('Helvetica', '20'))
    text.tag_configure('etf_tag', foreground='green', underline=True, font=('Helvetica', '20'))
    text.tag_configure('txt_tag', foreground='red', underline=True, font=('Helvetica', '20'))
    scrollbar.config(command=text.yview)
    result_window.bind('<Escape>', lambda e: (result_window.destroy(), sys.exit(0)))

    def open_file_and_change_tag_color(path, tag_name):
        open_file(path)
        text.tag_configure(tag_name, foreground='grey', underline=False)

    def open_json_file(tag_name):
        open_file(json_path)
        text.tag_configure(tag_name, foreground='grey', underline=False)

    if results:
        for directory, files in results.items():
            if files:
                text.insert("end", directory + "\n", 'directory_tag')
                for file in files:
                    file_path = os.path.join(directory, file)
                    tag_name = "link_" + file.replace(".", "_")
                    text.tag_bind(tag_name, "<Button-1>", lambda event, path=file_path, tag=tag_name: open_file_and_change_tag_color(path, tag))
                    text.insert("end", file + "\n", (tag_name, 'file_tag'))
                text.insert("end", "\n")
    else:
        text.insert("end", "没有找到包含关键词的文件。\n")

    if matched_names_stocks:
        text.insert("end", "匹配的Descreption里股票名称:\n", 'directory_tag')
        for name in matched_names_stocks:
            tag_name = "stock_" + name.replace(" ", "_")
            text.tag_bind(tag_name, "<Button-1>", lambda event, tag=tag_name: open_json_file(tag))
            text.insert("end", name + "\n", (tag_name, 'stock_tag'))
        text.insert("end", "\n") 

    if matched_names_etfs:
        text.insert("end", "匹配的Descreption里ETFs名称:\n", 'directory_tag')
        for name in matched_names_etfs:
            tag_name = "etf_" + name.replace(" ", "_")
            text.tag_bind(tag_name, "<Button-1>", lambda event, tag=tag_name: open_json_file(tag))
            text.insert("end", name + "\n", (tag_name, 'etf_tag'))
        text.insert("end", "\n") 

    if matched_names_txt:
        text.insert("end", "匹配的symbol_name里的股票名称:\n", 'directory_tag')
        for name in matched_names_txt:
            tag_name = "txt_" + name.replace(" ", "_")
            text.tag_bind(tag_name, "<Button-1>", lambda event, tag=tag_name: open_file_and_change_tag_color("/Users/yanzhang/Documents/News/backup/symbol_names.txt", tag))
            text.insert("end", name + "\n", (tag_name, 'txt_tag'))
        text.insert("end", "\n") 