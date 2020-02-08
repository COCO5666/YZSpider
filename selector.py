# -*- coding : utf-8 -*-
# @Author : Coco
# @Author's GitHub : https://github.com/COCO5666
# @Author's CSND : https://blog.csdn.net/COCO56
# @Author's Webpage : https://coco5666.github.io/
# @IDE: PyCharm
# @Python: Python3.7.2
# @Created Time :2019-02-16 21:49:29
# @Modified Time :2019-02-16 23:58:25
# @File : selector.py

"""
* 筛选器模块
* 为对采集到的数据进行筛选/过滤提供支持
"""

from designPattern import addGetInstanceFunc
from urllib import parse
from multiple import asyncRunFunc
import shutil
import os
from time import sleep
from V3_0.Spider.api import getHtmlTextData
from V3_0.Spider.Config.api import getDomain
from V3_0.Setting.api import asynFlag, poolNum
from V3_0.Storer.api import getDataBasePath, makeDir
from os.path import join


@addGetInstanceFunc
class selector:
	'''
    本类用于采集期间进行的数据筛选/过滤操作
    本类采用单例模式（通过designPattern.singleton装饰器来新建类的_instance属性，重写new方法，并对外提供getInstance接口）
    '''

	def __init__(self):
		# 创建原始数据网页文件保存的根目录
		self.htmlsRootPath = join(getDataBasePath(), 'htmls')
		makeDir(self.htmlsRootPath)
		self.indexHtmlsRootPath = self.htmlsRootPath + '//0000index'
		makeDir(self.indexHtmlsRootPath)
		# 创建pkl文件保存的根目录
		self.pklsRootPath = join(getDataBasePath(), 'pkls')
		makeDir(self.pklsRootPath)

	# 用于快速使用正则表达式提取所有数据
	def _findAllWithRe(self, data, pattern):
		from V3_0.Selector.api import findAllWithRe
		return findAllWithRe(data, pattern)

	def reSelect(self, flag, subjectsInfoPklPath):
		if flag:
			shutil.rmtree(self.pklsRootPath)
			if os.path.exists(subjectsInfoPklPath):
				os.remove(subjectsInfoPklPath)
			self.__init__()

	# 获取每一个学科类别的所有机构名
	def getInstitutionsName(self, SCs_data):
		data = {}
		for SC_code in SCs_data:
			value = SCs_data[SC_code]
			SC_name = value[0]
			index_htmls_Path = self.indexHtmlsRootPath + '//' + SC_code + '-' + SC_name
			self.storerIns.makeDir(index_htmls_Path)
			pagesURL = self._getPagesUrl(value)
			ins = [SC_name]
			temp = self._getInstitutions(pagesURL, index_htmls_Path)
			for t in temp:
				ins.append((t))
			dic = {SC_code: ins}
			data.update(dic)
		return data

	def _getPagesUrl(self, SC_data):
		urls = []
		# print(SC_data)
		max = int(SC_data[2])
		li = range(1, max + 1)
		for i in li:
			urls.append(SC_data[1] + '&pageno=' + str(i))
		return urls

	def _getInstitutions(self, pagesURL, index_htmls_Path):
		res2 = []
		cnt = 1
		for url in pagesURL:
			text = getHtmlTextData(url, index_htmls_Path + '//' + str(cnt))
			pattern = '<a href=".+?" target="_blank">\((\d+?)\)(.+?)</a>'
			res = self._findAllWithRe(text, pattern)
			res2.append(res)
			cnt += 1
		return res2

	def getAllSCInfo(self, SC_data):
		# 从pkl文件中获取逐一获取每一个学科类别的所有招生机构的招生数据
		final = []
		for SC_code in SC_data:
			value = SC_data[SC_code]
			SC_name = value[0]
			data = self._getSCInfoFromPklFile(SC_code, value)
			final.append(data)
		return final

	def _getSCInfoFromPklFile(self, SC_code, value):
		SC_code_and_name = SC_code + '-' + value[0]
		pkl_SC_path = self.pklsRootPath + '\\' + SC_code_and_name + '.pkl'
		para = (SC_code, value)
		return self.storerIns.getPickleFileDataFromOtherData(pkl_SC_path, self._getSCInfoFromHtmls, para)

	def _getSCInfoFromHtmls(self, para):
		'''
        :param para:
        :return:
            类型：列表
            元素：第一个元素为哨兵（保存学科类别代码与名称），其余元素为数据项
                其中：其余所有数据项为：datum = asyncRunFunc(self._asyncGetInstitutionInfo, paraList, asyn=False)
        '''
		(SC_code, value) = para
		SC_name = value[0]
		SC_code_and_name = SC_code + '-' + SC_name
		htmls_SC_Path = self.htmlsRootPath + '\\' + SC_code_and_name
		self.storerIns.makeDir(htmls_SC_Path)
		SC_instutions = value[1:]
		paraList = []
		final = (SC_code, SC_name)
		for page in SC_instutions:
			for ins in page:
				if ins == '':
					break
				ins_code = ins[0]
				ins_name = ins[1]
				ins_url = self._getInstitutionURL(SC_code, ins_name)
				html_ins_Path = htmls_SC_Path + '\\' + ins_code + '-' + ins_name
				para = (ins_code, ins_name, ins_url, html_ins_Path, htmls_SC_Path)
				paraList.append(para)
		datum = asyncRunFunc(self._asyncGetInstitutionInfo, paraList, poolNum=poolNum, asyn=asynFlag)
		datum.insert(0, final)
		return datum

	def _getInstitutionURL(self, SC_code, ins_name):
		url = getDomain() + '/zsml/querySchAction.do?dwmc='
		url += parse.quote(ins_name)
		url = url + '&yjxkdm=' + SC_code
		return url

	def _asyncGetInstitutionInfo(self, para):
		(ins_code, ins_name, ins_url, html_ins_Path, htmls_SC_Path) = para
		data = self._getInstitutionInfo(ins_code, ins_name, ins_url, html_ins_Path, htmls_SC_Path)
		return data

	def _getInstitutionInfo(self, ins_code, ins_name, ins_url, html_ins_Path, htmls_SC_Path):
		'''
        :param ins_code:
        :param ins_name:
        :param ins_url:
        :param html_ins_Path:
        :param htmls_SC_Path:
        :return:
            类型：列表
            元素：第一个元素为哨兵（保存机构代码与机构名），其余元素为数据项（每一个研究方向的具体信息）
                其中：每个数据项为：data = self._getResearchAreaData(i, htmls_RA_scopePath)
        '''
		# RA: resarch area
		htmls_RA_scope_Root_Path = htmls_SC_Path + '\\Scope'
		self.storerIns.makeDir(htmls_RA_scope_Root_Path)
		htmls_RA_scopePath = htmls_RA_scope_Root_Path + '\\' + ins_code + '-' + ins_name
		self.storerIns.makeDir(htmls_RA_scopePath)
		text = getHtmlTextData(ins_url, html_ins_Path)
		# ins_url = 'http://yz.chsi.com.cn/zsml/querySchAction.do?dwmc=%E5%8C%97%E4%BA%AC%E5%A4%A7%E5%AD%A6&yjxkdm=0252'
		# 获取表格
		pattern = '<tbody>(.+?)</tbody>'
		temp = self._findAllWithRe(text, pattern)[0]
		# 获取表格里的所有条数据
		pattern = '<tr>(.+?)</tr>'
		researchAreas_data = self._findAllWithRe(temp, pattern)
		# 从每一条数据里筛选出需要的信息
		final = []
		temp = [ins_code, ins_name, ins_url]
		final.append(temp)
		for i in researchAreas_data:
			data = self._getResearchAreaInfo(i, htmls_RA_scopePath)
			final.append(data)
		return final

	def _getResearchAreaInfo(self, rawData, htmls_RA_scopePath):
		'''
        :param rawData:
        :param htmls_RA_scopePath:
        :return:
            类型：列表
            列表内元素：考试方式、院系所、专业、研究方向、学习方式、指导教师、拟招生人数、考试范围的id、跨专业、备注、考试范围
                其中：为字符类型的有：考试方式、院系所、专业、研究方向、学习方式、指导教师、拟招生人数、考试范围的id、跨专业、备注
                    为元组类型的有：考试范围
        '''
		# 筛选出：考试方式、院系所、专业、研究方向、学习方式
		pattern = '>(.+?)</td>'
		temp = self._findAllWithRe(rawData, pattern)
		final = temp[:5]
		temp = temp[5:]
		# 筛选出：指导教师
		pattern = '<span.+?>(.+?)</span>'
		t = self._findAllWithRe(temp[0], pattern)
		final.append(t[0])
		temp = temp[1:]
		# 筛选出：拟招生人数
		pattern = "document.write\(cutString\(\'(.+?)\'"
		t = self._findAllWithRe(temp[0], pattern)
		final.append(t[0])
		temp = temp[1:]
		# 筛选出：考试范围的id及URL
		pattern = 'id=(.+?)"'
		scope_id = self._findAllWithRe(temp[0], pattern)[0]
		scope_url = getDomain() + '/zsml/kskm.jsp?id=' + scope_id
		schoolDepartment = final[1]
		schoolDepartment = schoolDepartment.replace('/', '或')
		researchArea = final[3]
		researchArea = researchArea.replace('/', '或')
		researchArea = researchArea.replace('\\', '或')
		researchArea = researchArea.replace('*', '')
		researchArea = researchArea.replace('?', '')
		researchArea = researchArea.replace('\n', '')
		researchArea = researchArea.replace('\t', '')
		researchArea = researchArea.replace('|', '_')
		scope_name = schoolDepartment + '-' + final[2] + '-' + researchArea
		scope_path = htmls_RA_scopePath + '\\' + scope_name
		if scope_url == getDomain() + '/zsml/kskm.jsp?id=':
			print(scope_url)
			print(scope_path)
			sleep(9999999999999)
		final.append(scope_id)
		temp = temp[1:]
		# 筛选出：跨专业
		pattern = '>(.+?)</a>'
		t = self._findAllWithRe(temp[0], pattern)
		final.append(t[0])
		temp = temp[1:]
		# 筛选出：备注
		pattern = "document.write\(cutString\(\'(.+?)\'"
		t = self._findAllWithRe(temp[0], pattern)
		final.append(t[0])
		temp = temp[1:]
		# 获取考试范围
		scopeData = self._getExamScope(scope_url, scope_path)
		final.append(scopeData)
		return final

	def _getExamScope(self, scope_url, scope_path):
		text = getHtmlTextData(scope_url, scope_path)
		# 获取表头
		pattern = '<th>(.+?)</th>'
		thead = self._findAllWithRe(text, pattern)
		# 获取表格内容
		pattern = '<tbody class="zsml-res-items">(.+?)</tbody>'
		tbody = self._findAllWithRe(text, pattern)
		temp = []
		temp.append(thead)
		for i in tbody:
			pattern = '.+?(\(.+?)\n.+?<span class="sub-msg">(.+?)</span>.+?'
			t = self._findAllWithRe(i, pattern)
			temp.append(t)
		return tuple(temp)
